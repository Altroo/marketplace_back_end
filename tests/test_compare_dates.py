from datetime import date


def test():
    mode_vacance_to = date(2022, 5, 31)
    today = date.today()
    if today > mode_vacance_to:
        print('>')
    else:
        print('<')


if __name__ == '__main__':
    test()
