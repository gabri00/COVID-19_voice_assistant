import requests
import json
import pyttsx3
import speech_recognition as sr
import re
import threading
import time

API_KEY = "trjG13bK9cAX"
PROJECT_TOKEN = "tT--XLK8sjQP"
RUN_TOKEN = "t5-R5fobXLvr"


class Data:
	def __init__(self, api_key, project_token):
		self.api_key = api_key
		self.project_token = project_token
		self.params = { "api_key": self.api_key }
		self.data = self.get_data()

	def get_data(self):
		response = requests.get(f'https://www.parsehub.com/api/v2/projects/{self.project_token}/last_ready_run/data', params=self.params)
		data = json.loads(response.text)
		return data

	def get_total_positives(self):
		data = self.data['totali']

		for content in data:
			if content['name'] == "Totale positivi":
				return content['data']

		return "0"

	def get_total_healed(self):
		data = self.data['totali']

		for content in data:
			if content['name'] == "Guariti":
				return content['data']

		return "0"

	def get_total_deaths(self):
		data = self.data['totali']

		for content in data:
			if content['name'] == "Deceduti":
				return content['data']

		return "0"


	def get_total_cases(self):
		data = self.data['totali']

		for content in data:
			if content['name'] == "Casi totali":
				return content['data']

		return "0"

	def get_region_data(self, region):
		data = self.data["regioni"]

		for content in data:
			if content['data_regioni'].lower().split(":")[0] == region.lower():
				return content

		return "0"

	def get_list_of_regions(self):
		regions = []
		for region in self.data['regioni']:
			regions.append(region['data_regioni'].lower().split(":")[0])

		return regions

	def update_data(self):
		response = requests.post(f'https://www.parsehub.com/api/v2/projects/{self.project_token}/run', params=self.params)

		def poll():
			time.sleep(0.1)
			old_data = self.data

			while True:
				new_data = self.get_data()

				if new_data != old_data:
					self.data = new_data
					print("Dati aggiornati")
					break

				else:
					print("I dati sono già i più recenti")

				time.sleep(5)


		t = threading.Thread(target = poll)
		t.start()


def speak(text, engine):
	engine.say(text)
	engine.runAndWait()


def get_audio():
	r = sr.Recognizer()

	with sr.Microphone() as source:
		audio = r.listen(source)
		said = ""

		try:
			said = r.recognize_google(audio, language="it-IT")
		except Exception as e:
			print("Exception:" + str(e))

	return said.lower()


def main():
	print("Program started... say something")

	data = Data(API_KEY, PROJECT_TOKEN)

	END_PATTERNS = [ "stop", "termina", "vai a dormire", "esci" ]

	region_list = data.get_list_of_regions()

	TOTAL_PATTERNS = {
					re.compile("[\w\s]+ casi [\w\s]+ totali"): data.get_total_cases,
					re.compile("[\w\s]+ casi totali"): data.get_total_cases,
                    re.compile("[\w\s]+ morti [\w\s]+ totali"): data.get_total_deaths,
                    re.compile("[\w\s]+ morti totali"): data.get_total_deaths,
                    re.compile("[\w\s]+ guariti [\w\s]+ totali"): data.get_total_healed,
                    re.compile("[\w\s]+ guariti totali"): data.get_total_healed,
                    re.compile("[\w\s]+ positivi [\w\s]+ totali"): data.get_total_positives,
                    re.compile("[\w\s]+ positivi totali"): data.get_total_positives
					}

	REGION_PATTERNS = {
					re.compile("[\w\s]+ casi [\w\s]+"): lambda region: data.get_region_data(region)['casi_totali'],
					re.compile("[\w\s]+ positivi [\w\s]+"): lambda region: data.get_region_data(region)['casi_positivi'],
					}

	UPDATE_COMMAND = re.compile("aggiorna[\w\s]+")

	engine = pyttsx3.init()
	engine.setProperty('rate', 135)
	voices = engine.getProperty('voices')
	engine.setProperty('voice', voices[0].id)

	while True:
		print("Listening...")

		text = get_audio()
		print(text)
		result = None

		for pattern, func in REGION_PATTERNS.items():
			if pattern.match(text):
				words = set(text.split(" "))

				for region in region_list:
					if region in words:
						result = func(region)
						break

		for pattern, func in TOTAL_PATTERNS.items():
			if pattern.match(text):
				result = func()
				break

		if re.match(UPDATE_COMMAND, text):
			data.update_data()
			result = "Dati in aggiornamento... attendere!"

		if result:
			speak(result, engine)

		for end in END_PATTERNS:
			if text.find(end) != -1:  # stop loop, find() returns -1 if it doesn't find anything
				print("Programma terminato")
				speak("Buonanotte", engine)
				exit()

main()
