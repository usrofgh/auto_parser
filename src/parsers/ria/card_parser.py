import math


class CardParser:
    def parse_card(self, root, card_url: str, phone_number: str | None) -> dict:

        obj = {
            "url": card_url,
            "title": self._parse_title(root),
            "price_usd": self._parse_price_usd(root),
            "odometer": self._parse_odometer(root),
            "username": self._parse_seller_name(root),
            "phone_number": phone_number,
            "image_url": self._parse_image_url(root),
            "images_count": self._parse_images_count(root),
            "car_number": self._parse_car_number(root),
            "car_vin": self._parse_car_vin(root)
        }
        return obj

    @staticmethod
    def _parse_title(root) -> str:
        return root.xpath("//h1/@title")[0].strip()

    @staticmethod
    def parse_count_of_pages(root) -> int:
        info = root.xpath("//script[contains(text(), 'window.ria.server.resultsCount')]")[0].text.strip()
        total_elements = int(info.split("window.ria.server.resultsCount = Number(")[-1].split(");")[0])
        total_pages = int(math.ceil(total_elements / 100))
        return total_pages

    @staticmethod
    def extract_data_hash(root) -> str:
        is_exist = root.xpath("//*[@data-hash]/@data-hash")
        if is_exist:
            return is_exist[0].strip()

    @staticmethod
    def extract_card_id(root) -> str:
        return root.xpath("//li[@id='addDate']/following-sibling::li[contains(text(), 'ID авто')]/span")[0].text.strip()

    @staticmethod
    def parse_card_links(root) -> list:
        links = root.xpath("//div[@class='head-ticket']//a/@href")
        return links

    @staticmethod
    def _parse_odometer(root) -> int:
        odometer_info = root.xpath("//div[@class='base-information bold']")[0].text_content().strip()
        if "без" in odometer_info:
            return 0
        odometer_value = int(odometer_info.split()[0])
        if "тис." in odometer_info:  # if > 999 km
            odometer_value *= 1000

        return odometer_value

    @staticmethod
    def _parse_car_number(root) -> str | None:

        car_number = None
        is_car_number_exist = root.xpath("//span[@class='state-num ua']")
        if is_car_number_exist:
            car_number = is_car_number_exist[0].text_content().strip()[:10].replace(" ", "").replace("-", "")

        return car_number

    @staticmethod
    def _parse_car_vin(root) -> str | None:
        car_vin = None
        is_car_vin_exist = root.xpath("//span[@class='label-vin']")
        if not is_car_vin_exist:
            is_car_vin_exist = root.xpath("//span[@class='vin-code']")
        if not is_car_vin_exist:
            is_car_vin_exist = root.xpath("//span[contains(@class, 'label-vin-code')]/following-sibling::span[1]")
        if is_car_vin_exist:
            car_vin = is_car_vin_exist[0].text_content().strip()
        return car_vin

    @staticmethod
    def _parse_price_usd(root) -> int:
        price_usd = root.xpath("//div[@class='price_value']/strong[contains(text(), '$')]")
        if not price_usd:
            price_usd = int(root.xpath("//div[@class='price_value--additional']//span[@data-currency='USD']")[0].text.strip().replace(" ", ""))
        else:
            price_usd = int(price_usd[0].text.replace(" ", "").strip().replace("$", ""))
        return price_usd

    @staticmethod
    def _parse_seller_name(root) -> str | None:
        seller_name = None

        base_selector = "//aside[@id='showLeftBarView']//section[@id='userInfoBlock']//div[@class='seller_info_area']/div[contains(@class, 'seller_info_name ')]"
        is_seller_exist = root.xpath(f"{base_selector}/a")

        if not is_seller_exist:
            is_seller_exist = root.xpath(base_selector)
        if not is_seller_exist:
            is_seller_exist = root.xpath("//h4/a")
            if is_seller_exist and not is_seller_exist[0].text:
                is_seller_exist = root.xpath("//h4/strong")
        if is_seller_exist:
            seller_name = is_seller_exist[0].text.strip()
        else:
            seller_name = None
        return seller_name

    @staticmethod
    def _parse_image_url(root) -> str | None:
        photo_url = None
        is_exist_photo = root.xpath("//div[@id='photosBlock']//source[1]/@srcset")
        if is_exist_photo:
            photo_url = is_exist_photo[0].strip()
        return photo_url

    @staticmethod
    def _parse_images_count(root) -> int:
        return int(root.xpath("//div[@class='count-photo left']//span[@class='mhide']")[0].text.strip("з ").strip())
