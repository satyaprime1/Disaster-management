import os
import requests
from datetime import datetime
from dotenv import load_dotenv


# ============================================================
# PROJECT ROOT / ENVIRONMENT
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

ENV_FILE = os.path.join(
    PROJECT_ROOT,
    ".env"
)

load_dotenv(ENV_FILE)


# ============================================================
# COPERNICUS DATA SPACE ENDPOINTS
# ============================================================

AUTH_URL = (
    "https://identity.dataspace.copernicus.eu/"
    "auth/realms/CDSE/protocol/openid-connect/token"
)

CATALOGUE_URL = (
    "https://catalogue.dataspace.copernicus.eu/"
    "odata/v1/Products"
)

DOWNLOAD_URL = (
    "https://download.dataspace.copernicus.eu/"
    "odata/v1/Products"
)


# ============================================================
# CLIENT
# ============================================================

class CDSEClient:

    def __init__(self):

        self.username = os.getenv("CDSE_USERNAME")
        self.password = os.getenv("CDSE_PASSWORD")

        if not self.username or not self.password:

            raise RuntimeError(
                "\n"
                "CDSE credentials not found.\n\n"
                f"Expected .env file:\n{ENV_FILE}\n\n"
                "It must contain:\n\n"
                "CDSE_USERNAME=your_email\n"
                "CDSE_PASSWORD=your_password\n"
            )

        self.username = self.username.strip()

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": "Disaster-Management-Live-Monitor/1.0",
            "Accept": "application/json"
        })

        self.token = None


    # ========================================================
    # AUTHENTICATION
    # ========================================================

    def authenticate(self):

        print("Authenticating with Copernicus Data Space...")

        payload = {
            "client_id": "cdse-public",
            "username": self.username,
            "password": self.password,
            "grant_type": "password"
        }

        try:

            response = requests.post(
                AUTH_URL,
                data=payload,
                headers={
                    "Content-Type":
                    "application/x-www-form-urlencoded"
                },
                timeout=60
            )

        except requests.RequestException as exc:

            raise RuntimeError(
                f"Unable to connect to CDSE authentication server:\n"
                f"{exc}"
            )


        if response.status_code != 200:

            raise RuntimeError(
                "\n"
                "CDSE authentication failed:\n"
                f"HTTP {response.status_code}\n"
                f"{response.text}\n"
            )


        try:

            data = response.json()

        except ValueError:

            raise RuntimeError(
                "CDSE returned an invalid authentication response:\n"
                + response.text
            )


        access_token = data.get("access_token")

        if not access_token:

            raise RuntimeError(
                "CDSE authentication response did not contain "
                "an access token."
            )


        self.token = access_token

        self.session.headers.update({
            "Authorization":
            f"Bearer {self.token}"
        })

        print("Authentication successful.")


    # ========================================================
    # ENSURE AUTHENTICATION
    # ========================================================

    def ensure_authenticated(self):

        if not self.token:

            self.authenticate()


    # ========================================================
    # SEARCH PRODUCTS
    # ========================================================

    def search_products(
        self,
        satellite,
        start_time,
        end_time,
        bbox,
        top=20
    ):

        self.ensure_authenticated()

        min_lon, min_lat, max_lon, max_lat = bbox


        # ----------------------------------------------------
        # FOOTPRINT
        # ----------------------------------------------------

        footprint = (
            "geography'SRID=4326;"
            "POLYGON(("
            f"{min_lon} {min_lat},"
            f"{max_lon} {min_lat},"
            f"{max_lon} {max_lat},"
            f"{min_lon} {max_lat},"
            f"{min_lon} {min_lat}"
            "))'"
        )


        # ----------------------------------------------------
        # SENTINEL-2
        # ----------------------------------------------------

        if satellite.upper() == "SENTINEL-2":

            collection_filter = (
                "Collection/Name eq 'SENTINEL-2'"
            )

            product_filter = (
                "Attributes/OData.CSC.StringAttribute/"
                "any(att:"
                "att/Name eq 'productType' "
                "and "
                "att/OData.CSC.StringAttribute/Value "
                "eq 'S2MSI2A')"
            )


        # ----------------------------------------------------
        # SENTINEL-1
        # ----------------------------------------------------

        elif satellite.upper() == "SENTINEL-1":

            collection_filter = (
                "Collection/Name eq 'SENTINEL-1'"
            )

            product_filter = (
                "Attributes/OData.CSC.StringAttribute/"
                "any(att:"
                "att/Name eq 'productType' "
                "and "
                "att/OData.CSC.StringAttribute/Value "
                "eq 'IW_GRDH_1S')"
            )


        else:

            raise ValueError(
                f"Unsupported satellite: {satellite}"
            )


        # ----------------------------------------------------
        # TIME
        # ----------------------------------------------------

        if start_time.tzinfo is None:

            start_time = start_time.replace(
                tzinfo=datetime.now().astimezone().tzinfo
            )

        if end_time.tzinfo is None:

            end_time = end_time.replace(
                tzinfo=datetime.now().astimezone().tzinfo
            )


        start_utc = start_time.astimezone().strftime(
            "%Y-%m-%dT%H:%M:%S.000Z"
        )

        end_utc = end_time.astimezone().strftime(
            "%Y-%m-%dT%H:%M:%S.000Z"
        )


        time_filter = (
            f"ContentDate/Start gt {start_utc}"
            f" and "
            f"ContentDate/Start lt {end_utc}"
        )


        # ----------------------------------------------------
        # SPATIAL
        # ----------------------------------------------------

        spatial_filter = (
            f"OData.CSC.Intersects(area={footprint})"
        )


        # ----------------------------------------------------
        # FINAL FILTER
        # ----------------------------------------------------

        query_filter = (
            f"{collection_filter} and "
            f"{product_filter} and "
            f"{time_filter} and "
            f"{spatial_filter}"
        )


        params = {
            "$filter": query_filter,
            "$orderby": "ContentDate/Start desc",
            "$top": top
        }


        try:

            response = self.session.get(
                CATALOGUE_URL,
                params=params,
                timeout=120
            )

        except requests.RequestException as exc:

            raise RuntimeError(
                f"CDSE product search connection failed:\n{exc}"
            )


        # ----------------------------------------------------
        # TOKEN EXPIRED
        # ----------------------------------------------------

        if response.status_code == 401:

            print(
                "CDSE token expired. "
                "Authenticating again..."
            )

            self.token = None

            self.authenticate()

            response = self.session.get(
                CATALOGUE_URL,
                params=params,
                timeout=120
            )


        if response.status_code != 200:

            raise RuntimeError(
                "\n"
                "CDSE product search failed:\n"
                f"HTTP {response.status_code}\n"
                f"{response.text}\n"
            )


        try:

            data = response.json()

        except ValueError:

            raise RuntimeError(
                "CDSE returned invalid catalogue JSON."
            )


        return data.get("value", [])


    # ========================================================
    # DOWNLOAD PRODUCT
    # ========================================================

    def download_product(
        self,
        product,
        output_directory
    ):

        self.ensure_authenticated()


        product_id = product.get("Id")
        product_name = product.get("Name")


        if not product_id:

            raise RuntimeError(
                "Satellite product has no Id."
            )

        if not product_name:

            raise RuntimeError(
                "Satellite product has no Name."
            )


        os.makedirs(
            output_directory,
            exist_ok=True
        )


        # ----------------------------------------------------
        # SAFE DOWNLOAD
        # ----------------------------------------------------

        archive_path = os.path.join(
            output_directory,
            product_name + ".zip"
        )


        url = (
            f"{DOWNLOAD_URL}"
            f"({product_id})/$value"
        )


        print()
        print("=" * 70)
        print("DOWNLOADING SATELLITE PRODUCT")
        print("=" * 70)

        print(f"Product: {product_name}")
        print(f"Product ID: {product_id}")


        total = product.get("ContentLength")


        if total:

            total = int(total)

            print(
                f"Size: "
                f"{total / (1024 ** 3):.2f} GB"
            )


        print()


        try:

            with self.session.get(
                url,
                stream=True,
                timeout=(60, 300)
            ) as response:


                # --------------------------------------------
                # TOKEN EXPIRED
                # --------------------------------------------

                if response.status_code == 401:

                    print(
                        "Download authorization expired."
                    )

                    self.token = None

                    self.authenticate()


                    with self.session.get(
                        url,
                        stream=True,
                        timeout=(60, 300)
                    ) as retry_response:

                        if retry_response.status_code != 200:

                            raise RuntimeError(
                                "Download failed after "
                                "reauthentication:\n"
                                f"HTTP "
                                f"{retry_response.status_code}\n"
                                f"{retry_response.text[:500]}"
                            )

                        return self._stream_download(
                            retry_response,
                            archive_path,
                            total
                        )


                if response.status_code != 200:

                    raise RuntimeError(
                        "Download failed:\n"
                        f"HTTP {response.status_code}\n"
                        f"{response.text[:500]}"
                    )


                return self._stream_download(
                    response,
                    archive_path,
                    total
                )


        except requests.RequestException as exc:

            # Remove incomplete file

            if os.path.exists(archive_path):

                try:
                    os.remove(archive_path)
                except OSError:
                    pass


            raise RuntimeError(
                f"Satellite product download failed:\n"
                f"{exc}"
            )


    # ========================================================
    # STREAM DOWNLOAD
    # ========================================================

    def _stream_download(
        self,
        response,
        archive_path,
        total
    ):

        downloaded = 0

        last_percent = -1


        with open(
            archive_path,
            "wb"
        ) as file:


            for chunk in response.iter_content(
                chunk_size=8 * 1024 * 1024
            ):

                if not chunk:
                    continue


                file.write(chunk)

                downloaded += len(chunk)


                if total:

                    percent = int(
                        downloaded * 100 / total
                    )

                    percent = min(
                        percent,
                        100
                    )


                    if percent != last_percent:

                        print(
                            f"\rProgress: "
                            f"{percent:3d}% "
                            f"("
                            f"{downloaded / (1024 ** 3):.2f}/"
                            f"{total / (1024 ** 3):.2f} GB"
                            f")",
                            end="",
                            flush=True
                        )

                        last_percent = percent


                else:

                    print(
                        f"\rDownloaded: "
                        f"{downloaded / (1024 ** 3):.2f} GB",
                        end="",
                        flush=True
                    )


        print()
        print("Download complete.")


        return archive_path

