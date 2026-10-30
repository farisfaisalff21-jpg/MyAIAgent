from agents import function_tool
import re


@function_tool
def create_content_plan(
    business_name: str,
    product: str,
    target_audience: str,
    platform: str,
) -> str:
    """Create a 7-day social media content plan for a business."""

    days = [
        ("Business introduction", "Introduce the business and its products."),
        ("Product benefits", "Explain a genuine benefit of the product."),
        ("Helpful tip", "Share a useful tip related to the product."),
        ("Audience engagement", "Ask the audience a relevant question."),
        ("Product showcase", "Suggest a creative product demonstration."),
        ("Behind the scenes", "Show how the business or product is prepared."),
        ("Call to action", "Invite people to learn more or get in touch."),
    ]

    plan = [
        "7-DAY SOCIAL MEDIA CONTENT PLAN",
        f"Business: {business_name}",
        f"Product/service: {product}",
        f"Target audience: {target_audience}",
        f"Platform: {platform}",
        "",
    ]

    for day_number, (theme, idea) in enumerate(days, start=1):
        plan.append(f"Day {day_number}: {theme}")
        plan.append(f"Post idea: {idea}")
        plan.append(
            f"Caption direction: Write an engaging caption about "
            f"{product} for {target_audience}."
        )
        plan.append("Call to action: Invite people to comment, learn more, or contact the business.")
        plan.append("")

    plan.append(
        "Do not invent customer reviews, discounts, product claims, "
        "or business results."
    )

    return "\n".join(plan)


@function_tool
def generate_caption(
    business_name: str,
    product: str,
    target_audience: str,
    platform: str,
    tone: str = "friendly",
) -> str:
    """Create a marketing caption brief for a specific platform and audience."""

    return (
        f"Create one original {tone} marketing caption for {business_name}. "
        f"Product/service: {product}. "
        f"Target audience: {target_audience}. "
        f"Platform: {platform}. "
        "Include a suitable call to action. Use appropriate language and "
        "emojis when suitable. Do not invent discounts, reviews, or claims."
    )


@function_tool
def generate_hashtags(
    product: str,
    target_audience: str,
    platform: str,
) -> str:
    """Suggest relevant hashtags for a product and target audience."""

    def words(value: str) -> list[str]:
        return re.findall(r"[a-zA-Z0-9]+", value.lower())

    product_tags = ["".join(words(product))]
    audience_tags = ["".join(words(target_audience))]
    platform_tags = {
        "instagram": ["InstagramMarketing", "InstaBusiness"],
        "facebook": ["FacebookMarketing", "SmallBusiness"],
        "tiktok": ["TikTokMarketing", "TikTokBusiness"],
        "linkedin": ["LinkedInMarketing", "BusinessGrowth"],
        "youtube": ["YouTubeMarketing", "ContentMarketing"],
    }

    tags = [
        "Marketing",
        "SmallBusiness",
        "ContentCreation",
        *product_tags,
        *audience_tags,
        *platform_tags.get(platform.strip().lower(), ["DigitalMarketing"]),
    ]

    unique_tags = []
    seen = set()

    for tag in tags:
        cleaned = re.sub(r"[^a-zA-Z0-9]", "", tag)
        if cleaned and cleaned.lower() not in seen:
            seen.add(cleaned.lower())
            unique_tags.append(f"#{cleaned}")

    return (
        f"Suggested hashtags for {platform}:\n"
        + " ".join(unique_tags)
        + "\nThese are suggestions, not a guarantee of reach or engagement."
    )