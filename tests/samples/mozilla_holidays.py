import os

import ics

PREFIX = "https://www.thunderbird.net"
URLS = [
    "/media/caldata/AlgeriaHolidays.ics",
    "/media/caldata/ArgentinaHolidays.ics",
    "/media/caldata/AustraliaHolidays.ics",
    "/media/caldata/AustrianHolidays.ics",
    "/media/caldata/BasqueHolidays.ics",
    "/media/caldata/BelgianHolidays.ics",
    "/media/caldata/BelgianDutchHolidays.ics",
    "/media/caldata/BelgianFrenchHolidays.ics",
    "/media/caldata/BoliviaHolidays.ics",
    "/media/caldata/BrazilHolidays.ics",
    "/media/caldata/BulgarianHolidays.ics",
    # "/media/caldata/CanadaHolidays.ics",
    "/media/caldata/CanadaQuebecHolidays.ics",
    "/media/caldata/ChileHolidays.ics",
    "/media/caldata/ChinaHolidays.ics",
    "/media/caldata/ChinaPublicHolidays.ics",
    "/media/caldata/ColombianHolidays.ics",
    "/media/caldata/CostaRicaHolidays.ics",
    "/media/caldata/CroatiaHolidays.ics",
    "/media/caldata/CzechHolidays.ics",
    "/media/caldata/DanishHolidays.ics",
    "/media/caldata/DominicanRepublicSpanish.ics",
    "/media/caldata/EstoniaHolidays.ics",
    "/media/caldata/FinlandHolidays.ics",
    "/media/caldata/FinlandHolidaysSwedish.ics",
    "/media/caldata/FlandersHolidays.ics",
    "/media/caldata/FrenchHolidays.ics",
    "/media/caldata/FrisianHolidays.ics",
    "/media/caldata/GermanHolidays.ics",
    "/media/caldata/GreeceHolidays.ics",
    "/media/caldata/GuyanaHolidays.ics",
    "/media/caldata/HaitiHolidays.ics",
    "/media/caldata/HongKongHolidays.ics",
    "/media/caldata/HungarianHolidays.ics",
    "/media/caldata/IcelandHolidays.ics",
    "/media/caldata/IndiaHolidays.ics",
    "/media/caldata/IndonesianHolidays.ics",
    "/media/caldata/IndonesianHolidaysEnglish.ics",
    "/media/caldata/IranHolidays_English.ics",
    "/media/caldata/IranHolidays_Persian.ics",
    "/media/caldata/IrelandHolidays2014-2021.ics",
    "/media/caldata/ItalianHolidays.ics",
    "/media/caldata/JapanHolidays.ics",
    "/media/caldata/KazakhstanHolidaysEnglish.ics",
    "/media/caldata/KazakhstanHolidaysRussian.ics",
    "/media/caldata/KenyaHolidays.ics",
    "/media/caldata/LatviaHolidays.ics",
    "/media/caldata/LiechtensteinHolidays.ics",
    "/media/caldata/LithuanianHolidays.ics",
    "/media/caldata/LuxembourgHolidays.ics",
    "/media/caldata/MoroccoHolidays.ics",
    "/media/caldata/DutchHolidays.ics",
    "/media/caldata/DutchHolidaysEnglish.ics",
    "/media/caldata/NewZealandHolidays.ics",
    "/media/caldata/NicaraguaHolidays.ics",
    "/media/caldata/NorwegianHolidays.ics",
    "/media/caldata/PakistanHolidays.ics",
    "/media/caldata/PeruHolidays.ics",
    "/media/caldata/PhilippinesHolidays.ics",
    "/media/caldata/PolishHolidays.ics",
    "/media/caldata/PortugalHolidays.ics",
    "/media/caldata/QueenslandHolidays.ics",
    "/media/caldata/RomaniaHolidays.ics",
    "/media/caldata/RussiaHolidays.ics",
    "/media/caldata/SingaporeHolidays.ics",
    "/media/caldata/SlovakHolidays.ics",
    "/media/caldata/SlovenianHolidays.ics",
    "/media/caldata/SouthAfricaHolidays.ics",
    "/media/caldata/SouthKoreaHolidays.ics",
    "/media/caldata/SpanishHolidays.ics",
    "/media/caldata/SriLankaHolidays.ics",
    "/media/caldata/SwedishHolidays.ics",
    "/media/caldata/SwissHolidays.ics",
    "/media/caldata/TaiwanHolidays.ics",
    "/media/caldata/ThaiHolidays.ics",
    "/media/caldata/TrinidadTobagoHolidays.ics",
    "/media/caldata/TurkeyHolidays.ics",
    "/media/caldata/UKHolidays.ics",
    "/media/caldata/USHolidays.ics",
    "/media/caldata/UkraineHolidays.ics",
    "/media/caldata/UruguayHolidays.ics",
    "/media/caldata/VietnamHolidays.ics",
]

if __name__ == "__main__":
    import requests
    import sh

    cal = ics.Calendar()

    for url in URLS:
        print(url)
        cal.events.extend(ics.Calendar(requests.get(PREFIX + url).text).events)

    print(cal)
    p = os.path.abspath("../../holidays.ics")
    print(p)
    with open(p, "w") as f:
        f.writelines(cal)
    print(sh.ls("-la", p))
    print(sh.wc("-l", p))
