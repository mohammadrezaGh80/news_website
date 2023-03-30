from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def control_query_param(context, key, value, full_path):
    if "?" in full_path:
        query_params = full_path[full_path.find("?") + 1:].split("&")
        key_query_params = [keyword.split('=')[0] for keyword in query_params]
        if key in key_query_params:
            current_value = context["request"].GET.get(key)
            query_params.remove(f"{key}={current_value}")
            if value != current_value:
                query_params.append(f"{key}={value}")

            if len(query_params) == 0:
                full_path = full_path[:full_path.find("?")]
            else:
                full_path = full_path[:full_path.find("?") + 1] + "&".join(query_params)
        else:
            full_path += f"&{key}={value}"
    else:
        full_path += f"?{key}={value}"
    return full_path
