from tools.image_generation import create_marketing_image


def main():
    result = create_marketing_image(
        prompt=(
            "Create a cheerful bakery advertisement featuring "
            "fresh cupcakes and cookies on a wooden table. "
            "Use warm lighting and a colorful professional "
            "social media style. Do not include text or logos."
        ),
        filename="bakery_test",
    )

    print(result)


if __name__ == "__main__":
    main()