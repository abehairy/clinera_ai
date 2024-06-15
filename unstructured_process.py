from unstructured_client import UnstructuredClient
from unstructured_client.models import shared
from unstructured_client.models.errors import SDKError

# Update here with your api key and server url
client = UnstructuredClient(
    api_key_auth="vrRo9LmavvdYV0OIpYUmF6tQdgbVYG",
    # server_url="YOUR_API_URL",
)

# Update here with your filename
filename = "data/New Era? 'Double Selective' Antibiotic Spares the Microbiome.html"

with open(filename, "rb") as f:
    files=shared.Files(
        content=f.read(),
        file_name=filename,
    )

# You can choose fast, hi_res or ocr_only for strategy, learn more in the docs at step 4
req = shared.PartitionParameters(files=files, strategy="auto")

try:
    resp = client.general.partition(req)
    pprint(json.dumps(resp.elements, indent=2))
except SDKError as e:
    print(e)
