import os


def expression_image_upload_to(instance, filename):
    """Upload to 'store/image/expression/<subtitle.video.slug>/<filename>'."""
    if instance.subtitle and instance.subtitle.video:
        video_slug = instance.subtitle.video.slug
    else:
        video_slug = 'no_video'

    # Clean filename to avoid weird characters
    base, ext = os.path.splitext(filename)
    safe_filename = f'{base}{ext}'

    return f'store/image/expression/{video_slug}/{safe_filename}'
