#!/usr/bin/python3

def getListings(driver):
	driver.get("https://vuokraovi.com")
	search_box = driver.get_element_by_xpath("""//*[@id="inputLocationOrRentalUniqueNo"]""")
	search_button = driver.get_element_by_xpath("""//*[@id="frontPageSearchPanelRentalsForm"]/div[4]/div[1]/button""")

	search_box.send_keys("Helsinki"+Keys.Enter)
