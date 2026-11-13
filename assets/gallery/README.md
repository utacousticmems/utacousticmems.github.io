# Gallery photos

Every photo in these folders appears on the website's [Gallery page](https://utacousticmems.github.io/gallery/) about a minute after you upload it. One folder is one album.

## Add photos

1. Open the album folder here on GitHub (for example `team-building`).
2. Click **Add file → Upload files** and drag your photos in (up to 100 at a time).
3. Click **Commit changes**.

## Before you upload

- **JPG or PNG only.** iPhone `.HEIC` files do not show in most browsers. Export them as JPEG first.
- **Shrink big photos.** A phone photo is often 3 to 8 MB. Resize it to about 2400 pixels on the long side (usually under 1 MB) so the page loads quickly and the site stays within GitHub's 1 GB limit. On a Mac: open the photo in Preview, **Tools → Adjust Size**, then **File → Export** as JPEG.
- **Name files so they sort by date,** such as `2026-10-lake-travis-1.jpg`. Lowercase, hyphens, no spaces. The newest name is shown first, and the first photo of an album is shown large.
- **This site is public.** Upload a photo only if everyone in it is fine with being shown. Nothing with unpublished results, proposal text, or anything under NDA or export control on a screen, whiteboard or bench in the background.

## Start a new album

On the `assets/gallery` page click **Add file → Upload files** and drag in a whole folder of photos. The folder name becomes the album name (`summer-bbq-2026` is shown as "Summer bbq 2026"). To set a nicer title, a description or the order of albums, add the folder to `_data/gallery.yml`.

## Captions (optional)

In `_data/gallery.yml`, under the album, add a line per photo:

```yaml
- folder: team-building
  title: Team building
  captions:
    2026-10-lake-travis-1.jpg: Kayaking on Lake Travis, October 2026
```

## Remove a photo

Open the photo on GitHub, click the **…** menu at the top right, then **Delete file** and **Commit changes**.
