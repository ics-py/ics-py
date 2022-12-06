import os

from ics import Calendar

ICAL_DIRECTORY = "/path/to/ics/directory"

# https://github.com/ics-py/ics-py/discussions/278#discussioncomment-2023338
def cal_from_file(
    filename: str, prodid: str = "PRODID:-//placeholder//text//EN\n"
) -> Calendar:
    buf = []

    with open(filename) as f:
        i = 0
        vcal = -1
        missing_prodid = True

        for line in f:
            buf.append(line)

            if line == "BEGIN:VCALENDAR\n":
                vcal = i
                missing_prodid = True
            elif line == "END:VCALENDAR\n":
                if missing_prodid:
                    # print(f'VCALENDAR without PRODID on line {vcal} in {filename}.')
                    buf[vcal] = buf[vcal] + prodid
                vcal = -2
            elif vcal != -1 and missing_prodid and line.startswith("PRODID:"):
                missing_prodid = False
            i += 1

        if vcal == -1:
            raise TypeError(f"{filename} is not an ics file")  # FIXME
        elif vcal >= 0 and missing_prodid:
            # print(f'VCALENDAR without PRODID nor end on line {vcal} in {filename}.')
            buf[vcal] = buf[vcal] + prodid

    return Calendar("".join(buf))


os.chdir(ICAL_DIRECTORY)

for i in os.listdir():
    try:
        cal_from_file(i)
    except Exception as e:
        print(f"NOK: {i}, {e}")
    else:
        print(f"OK: {i}")
