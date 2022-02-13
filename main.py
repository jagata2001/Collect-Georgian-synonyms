from scrap_class import ScrapGeorgianSynonyms

if __name__ == "__main__":
    url = "http://www.nplg.gov.ge/gwdict/index.php?a=list&d=17&p=1"
    scrap = ScrapGeorgianSynonyms(url)
    scrap.run()
