from flask import Flask, render_template, request
import json

app = Flask(__name__)
scenario = ''
playingScenario = False
startingQuestionId = ''

@app.route('/')
def menu():
    global playingScenario
    playingScenario = False
    return render_template('menu.html')


@app.route('/start')
def start():
    global scenario
    scenario = {
        'id': 0,
        'name': 'Scenariusz Podróży',
        'questions': [
            {
                'id': 0,
                'text': 'Jaka jest średnia wysokość gór w miejscu docelowym?',
                'optionalText': [

                ],
                'answers': [
                    {
                        'id': 0,
                        'text': 'Poniżej 1000 m n.p.m.',
                        'questionId': 1,
                    },
                    {
                        'id': 1,
                        'text': 'Powyżej 1000 m n.p.m.',
                        'questionId': 2,
                    },
                ]
            },
            {
                'id': 1,
                'text': 'Na taką wycieczkę powinno wystarczyć przygotowanie we własnym zakresie. Warto jednak zapoznać się ze szczegółowymi informacjami odnośnie docelowego szczytu.',
                'optionalText': [

                ],
                'answers': [
                    {
                        'id': 0,
                        'text': 'Dalej',
                        'questionId': 3,
                    }
                ]
            },
            {
                'id': 2,
                'text': 'Zalecane jest odpowiednie przygotowanie pod docelowy szczyt. Dobrze jest mieć doświadczenie w wędrówkach po górach lub zasięgnąć rady osób doświadczonych.',
                'optionalText': [

                ],
                'answers': [
                    {
                        'id': 0,
                        'text': 'Dalej',
                        'questionId': 3,
                    }
                ]
            },
            {
                'id': 3,
                'text': 'Czy planujesz po drodze pozwiedzać miejscowości znajdujące się na trasie podróży?',
                'optionalText': [

                ],
                'answers': [
                    {
                        'id': 0,
                        'text': 'Tak',
                        'questionId': 7,
                    },
                    {
                        'id': 1,
                        'text': 'Nie',
                        'questionId': 10,
                    },
                ]
            },
            {
                'id': 4,
                'text': 'Rodzaj akwenu?',
                'optionalText': [

                ],
                'answers': [
                    {
                        'id': 0,
                        'text': 'Jezioro',
                        'questionId': 5,
                    },
                    {
                        'id': 1,
                        'text': 'Morze',
                        'questionId': 6,
                    },
                ]
            },
            {
                'id': 5,
                'text': 'Ta opcja pozwala na większy wybór miejsca docelowego. W razie napiętego budżetu można zaoszczędzić na dojeździe.',
                'optionalText': [

                ],
                'answers': [
                    {
                        'id': 0,
                        'text': 'Dalej',
                        'questionId': 3,
                    }
                ]
            },
            {
                'id': 6,
                'text': 'Lepiej wcześniej poszukać mniej popularnych miejsc oraz zapoznać się z zaleceniami odnośnie bezpieczeństwa.',
                'optionalText': [

                ],
                'answers': [
                    {
                        'id': 0,
                        'text': 'Dalej',
                        'questionId': 3,
                    }
                ]
            },
            {
                'id': 7,
                'text': 'Jaka jest wielkość miejscowości docelowej?',
                'optionalText': [

                ],
                'answers': [
                    {
                        'id': 0,
                        'text': 'Miasto',
                        'questionId': 8,
                    },
                    {
                        'id': 1,
                        'text': 'Wieś',
                        'questionId': 9,
                    },
                ]
            },
            {
                'id': 8,
                'text': 'Warto sprawdzić oferty okresowych biletów komunikacji miejskiej. Możesz również poszukać  informacji o muzeach i innych większych ośrodkach kulturowych i turystycznych.',
                'optionalText': [

                ],
                'answers': [
                    {
                        'id': 0,
                        'text': 'Dalej',
                        'questionId': 10,
                    }
                ]
            },
            {
                'id': 9,
                'text': 'Dobrym pomysłem jest podróż samochodem. Warto również wcześniej zaopatrzyć się w przedmioty trudniej dostępne w mniejszych miejscowościach.',
                'optionalText': [

                ],
                'answers': [
                    {
                        'id': 0,
                        'text': 'Dalej',
                        'questionId': 10,
                    }
                ]
            },
            {
                'id': 10,
                'text': 'Czy cel podróży jest za granicą?',
                'optionalText': [

                ],
                'answers': [
                    {
                        'id': 0,
                        'text': 'Tak',
                        'questionId': 11,
                    },
                    {
                        'id': 1,
                        'text': 'Nie',
                        'questionId': 15,
                    },
                ]
            },
            {
                'id': 11,
                'text': 'Zaopatrz się w odpowiednią walutę i zapoznaj z podstawowym prawem w danym kraju.',
                'optionalText': [

                ],
                'answers': [
                    {
                        'id': 0,
                        'text': 'Dalej',
                        'questionId': 12,
                    }
                ]
            },
            {
                'id': 12,
                'text': 'Czy kraj docelowy sąsiaduje z twoim?',
                'optionalText': [

                ],
                'answers': [
                    {
                        'id': 0,
                        'text': 'Tak',
                        'questionId': 13,
                    },
                    {
                        'id': 1,
                        'text': 'Nie',
                        'questionId': 14,
                    },
                ]
            },
            {
                'id': 13,
                'text': 'Najprostszą formą transportu będzie samochód, autobus lub pociąg.',
                'optionalText': [

                ],
                'answers': [
                    {
                        'id': 0,
                        'text': 'Dalej',
                        'questionId': 15,
                    }
                ]
            },
            {
                'id': 14,
                'text': 'Możesz zorientować się w alternatywnych formach transportu jak np. samolot.',
                'optionalText': [

                ],
                'answers': [
                    {
                        'id': 0,
                        'text': 'Dalej',
                        'questionId': 15,
                    }
                ]
            },
            {
                'id': 15,
                'text': 'Jaka jest długość podróży?',
                'optionalText': [

                ],
                'answers': [
                    {
                        'id': 0,
                        'text': '1 dzień.',
                        'questionId': 16,
                    },
                    {
                        'id': 0,
                        'text': '2-4 dni',
                        'questionId': 17,
                    },
                    {
                        'id': 0,
                        'text': '1 tydzień',
                        'questionId': 18,
                    }
                ]
            },
            {
                'id': 16,
                'text': 'Jeśli nie planujesz noclegu wyjedź bardzo wcześnie rano, aby mieć jak najwięcej czasu w miejscu docelowym.',
                'optionalText': [

                ],
                'answers': [
                    {
                        'id': 0,
                        'text': 'Dalej',
                        'questionId': 19,
                    }
                ]
            },
            {
                'id': 17,
                'text': 'Poszukaj ofert noclegowych w miejscach blisko atrakcji turystycznych. Ze względu na krótki czas wycieczki nie musisz bardzo oszczędzać na noclegu.',
                'optionalText': [

                ],
                'answers': [
                    {
                        'id': 0,
                        'text': 'Dalej',
                        'questionId': 19,
                    }
                ]
            },
            {
                'id': 18,
                'text': 'Przy dłuższym pobycie dobrze jest poszukać tańszych ofert noclegowych.',
                'optionalText': [

                ],
                'answers': [
                    {
                        'id': 0,
                        'text': 'Dalej',
                        'questionId': 19,
                    }
                ]
            },
            {
                'id': 19,
                'text': 'Jaki jest klimat w miejscu docelowym?',
                'optionalText': [

                ],
                'answers': [
                    {
                        'id': 0,
                        'text': 'Ciepły',
                        'questionId': 20,
                    },
                    {
                        'id': 0,
                        'text': 'Chłodny',
                        'questionId': 21,
                    }
                ]
            },
            {
                'id': 20,
                'text': 'Spakuj lekkie ubranie, ale nie zapomnij o czymś przeciwdeszczowym oraz czymś grubszym na chłodne wieczory.',
                'optionalText': [
                    {
                        'text': 'Pamiętaj o stroju kąpielowym.',
                        'conditionalQuestionId': 4,
                    }
                ],
                'answers': [
                    {
                        'id': 0,
                        'text': 'Dalej',
                        'questionId': 22,
                    }
                ]
            },
            {
                'id': 21,
                'text': 'Zabierz dużo warstw ubrań. Lepiej wziąć za dużo niż potem marznąć.',
                'optionalText': [
                    {
                        'text': 'Wybierz odpowiednie obuwie do klimatu.',
                        'conditionalQuestionId': 0,
                    }
                ],
                'answers': [
                    {
                        'id': 0,
                        'text': 'Dalej',
                        'questionId': 22,
                    }
                ]
            },
            {
                'id': 21,
                'text': 'Gratulacje! Udało ci się przygotować do podróży.',
                'optionalText': [

                ],
                'answers': [
                ]
            }
        ]
    }
    with open("test_scenario.json", "w") as write_file:
        json.dump(scenario, write_file)

    with open("test_scenario.json", "r") as read_file:
        scenario = json.load(read_file)
    return render_template('start.html')


@app.route('/scenario')
def scenario():
    global scenario, playingScenario, startingQuestionId

    id = request.args.get('id')
    id = int(id)

    if playingScenario == False:
        startingQuestionId = id
        playingScenario = True

    return render_template('scenario.html', scenario=scenario, id=id, startingQuestionId=startingQuestionId)


if __name__ == '__main__':
    app.run()
