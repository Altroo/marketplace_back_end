
def test_4():
    list_of_cities = ['Casablanca', 'Oujda', 'Meknès', 'Oujda', 'Meknès', 'El Jadida']
    list_of_prices = [10, 10, 10, 15, 15, 20]
    list_of_days = [5, 5, 5, 6, 6, 9]

    new_result = list(zip(list_of_cities, list_of_prices, list_of_days))
    groups = {}
    for d in new_result:
        if d[0] not in groups:
            groups[d[0]] = {'price': d[1], 'days': d[2]}
        else:
            if groups[d[0]]['price'] < d[1]:
                groups[d[0]]['price'] = d[1]
            if groups[d[0]]['days'] < d[2]:
                groups[d[0]]['days'] = d[2]

    def deliveries_merge(deliveries):
        output = []
        unique_shifts = {}
        for key, val in deliveries.items():
            if str(val) not in unique_shifts.keys():
                unique_shifts[str(val)] = len(output)
                output.append(
                    {
                        "cities": [str(key)],
                        "price": val['price'],
                        "days": val['days']
                    }
                )
            else:
                output[unique_shifts[str(val)]]["cities"].append(str(key))
        return output
    results = deliveries_merge(groups)
    print(results)


if __name__ == '__main__':
    test_4()
