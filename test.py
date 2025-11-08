from algo import extract_preferences

mock_context = '{"message":"Jesse Bailey is a 50-year-old investor who started investing in 2016-05-17. His investment end date was 2018-02-15. His hobbies include learning languages, and he avoids energy and transportation, crypto assets, and life sciences. His true salary is $274484."}'

def test_extract_preferences():
    input_message = eval(mock_context)["message"]

    input_message = extract_preferences(input_message)

    print(f"input_message: {input_message}")


if __name__ == "__main__":
    test_extract_preferences()
    
    print(f"Test completed ...")

