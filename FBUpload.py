import time
import requests
from dotenv import load_dotenv
import os

load_dotenv()

PAGE_ID= os.getenv("PAGE_ID")
PAGE_ACCESS_TOKEN= os.getenv("PAGE_ACCESS_TOKEN")
API_VERSION= os.getenv("API_VERSION")
IG_USER_ID= os.getenv("IG_USER_ID")

# -------------------------------------------------
# get_schedule_time
# -------------------------------------------------

def get_schedule_time(hours=0, minutes=0):
    """
    Returns a Unix timestamp for the scheduled publish time.
    """
    # time.time() → current epoch seconds (float)
    # Convert to int for the API, then add the offset supplied by the caller.
    return int(time.time()) + (hours * 3600) + (minutes * 60)

# -------------------------------------------------
# schedule_photo_after
# -------------------------------------------------
def schedule_photo_after(image_path, caption = "", hours=0, minutes=0):
    """
    Schedule a post after the specified duration.
    """
    # 1️⃣ Compute the future publish timestamp using the helper above.
    publish_time = get_schedule_time(hours, minutes)

    # 2️⃣ Call the lower‑level API wrapper that actually uploads the photo.
    result = schedule_photo(image_path, caption, publish_time)

    # 3️⃣ Extract the Facebook‑generated photo ID from the JSON response.
    fb_photo_id = result.get("id")

    # 4️⃣ If the ID is missing the upload failed → raise an exception with details.
    if not fb_photo_id:
        raise Exception(f"Facebook upload failed: {result}")

    # 5️⃣ Build the URL that returns metadata (including CDN URLs) for the photo.
    photo_info_url = f"https://graph.facebook.com/{API_VERSION}/{fb_photo_id}"

    # 6️⃣ Request the photo metadata, asking only for the “images” field.
    photo_res = requests.get(
        photo_info_url,
        params={"fields": "images", "access_token": PAGE_ACCESS_TOKEN},
    )

    # 7️⃣ Parse the JSON and pull the list of available image variants.
    images = photo_res.json().get("images", [])

    # 8️⃣ If the list is empty something went wrong → raise.
    if not images:
        raise Exception("Could not retrieve image URL from Facebook photo response.")

    # 9️⃣ Return the highest‑resolution image URL (first element in the list).
    return images[0]["source"]

# -------------------------------------------------
# schedule_photo
# -------------------------------------------------

def schedule_photo(image_path, caption, publish_time):
    """
    Schedules a photo post on a Facebook Page.
    """
    # Build the endpoint URL for uploading a photo to the page.
    url = f"https://graph.facebook.com/{API_VERSION}/{PAGE_ID}/photos"

    # Open the image file in binary mode so it can be streamed to the API.
    with open(image_path, "rb") as image:
        # POST the multipart/form‑data request.
        response = requests.post(
            url,
            files={"source": image},               # The actual image bytes.
            data={
                "caption": caption,                # Optional text under the photo.
                # “false” tells Facebook to keep the post unpublished
                # so we can schedule it for a later time.
                "published": "true",
                # The epoch timestamp when the post should go live.
                # "scheduled_publish_time": publish_time,
                "access_token": PAGE_ACCESS_TOKEN,
            },
        )
    # Print the HTTP status for quick debugging (200 = OK).
    print(response.status_code)

    # Return the parsed JSON payload (contains the new photo’s ID, etc.).
    return response.json()

# -------------------------------------------------
# post_to_instagram_from_fb_url
# -------------------------------------------------
def post_to_instagram_from_fb_url(fb_image_url, caption=""):
    """
    Uses the Facebook CDN image URL to create and publish an Instagram container.
    """
    # 1️⃣ Create a media container on Instagram (the “draft” object).
    container_url = f"https://graph.facebook.com/{API_VERSION}/{IG_USER_ID}/media"
    container_res = requests.post(
        container_url,
        data={
            "image_url": fb_image_url,   # Direct CDN URL of the image we just uploaded.
            "caption": caption,          # Caption that will appear on Instagram.
            "access_token": PAGE_ACCESS_TOKEN,
        },
    ).json()

    # Grab the container ID; if missing the request failed.
    creation_id = container_res.get("id")
    if not creation_id:
        raise Exception(f"IG Container Creation Failed: {container_res}")

    # 2️⃣ Small pause – Meta needs a few seconds to finish processing the container.
    time.sleep(3)

    # 3️⃣ Publish the container, turning the draft into a live Instagram post.
    publish_url = (
        f"https://graph.facebook.com/{API_VERSION}/{IG_USER_ID}/media_publish"
    )
    publish_res = requests.post(
        publish_url,
        data={
            "creation_id": creation_id,
            "access_token": PAGE_ACCESS_TOKEN,
        },
    ).json()

    # Return the final response (contains the Instagram post ID, etc.).
    return publish_res

# -------------------------------------------------
# __main__ block
# -------------------------------------------------
if __name__ == "__main__":
    # Upload the image to Facebook, schedule it (here immediate), and get the CDN URL.
    fb_cdn_url = schedule_photo_after(
        image_path="image.jpg",
        minutes=0,
        hours=0
    )
    # Use that CDN URL to create and publish the Instagram post.
    post_to_instagram_from_fb_url(fb_cdn_url)