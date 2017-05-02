def get_latest_live_framework(all_frameworks, framework_type):
    try:
        latest = max(
            (f for f in all_frameworks if f['status'] == 'live' and f['framework'] == framework_type),
            key=lambda f: f['id'],
        )
        return latest
    except ValueError:  # max of empty iterable
        return None


def get_lots_by_slug(framework_data):
    return {lot['slug']: lot for lot in framework_data['lots']}


def is_g9_live(all_frameworks):
    """
    :return: True iff G8 is no longer the latest live G-Cloud framework.
    """
    framework = get_latest_live_framework(all_frameworks, 'g-cloud')
    return (framework['slug'] != 'g-cloud-8') if framework else False
