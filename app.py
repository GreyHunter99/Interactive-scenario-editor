from flask import Flask, render_template, request
import json
import os
import example

app = Flask(__name__)

scenario = ''
playingScenario = False
startingQuestionId = ''
scenarioList = {}

@app.route('/')
def menu():
    global scenarioList

    scenarioList = {}
    for scenario in os.listdir("database/scenarios/"):
        currentScenario = loadFromDatabase(scenario)
        scenarioList.update(currentScenario)

    global playingScenario
    playingScenario = False
    return render_template('menu.html')


@app.route('/list')
def list():
    global scenarioList

    return render_template('list.html', scenarioList=scenarioList)


@app.route('/start')
def start():
    global scenarioList, scenario

    #saveToDatabase("test_scenario.json", example.data)
    #scenario = loadFromDatabase("test_scenario.json")

    scenarioId = request.args.get('scenarioId')

    scenario = scenarioList[scenarioId]

    return render_template('start.html', scenario=scenario)


@app.route('/scenario')
def question():
    global scenario, playingScenario, startingQuestionId

    questionId = request.args.get('questionId')

    if playingScenario == False:
        startingQuestionId = int(questionId)
        playingScenario = True

    return render_template('question.html', scenario=scenario, questionId=questionId, startingQuestionId=startingQuestionId)

@app.route('/createScenario')
def createScenario():
    global scenarioList

    return render_template('editScenario.html')

@app.route('/editScenario')
def editScenario():
    global scenario

    scenarioId = request.args.get('scenarioId')

    scenario = scenarioList[scenarioId]

    return render_template('editScenario.html', scenario=scenario)


@app.route('/edit')
def edit():
    global scenario
    questionId = request.args.get('questionId')

    return render_template('edit.html', scenario=scenario, questionId=questionId)


def saveToDatabase(name, scenario):
    "Funkcja zapisująca scenariusz do bazy"
    with open("database/scenarios/"+name, "w") as write_file:
        json.dump(scenario, write_file)


def loadFromDatabase(name):
    "Funkcja wczytująca scenariusz z bazy"
    with open("database/scenarios/"+name, "r") as read_file:
        scenario = json.load(read_file)
    return scenario


if __name__ == '__main__':
    app.run(debug = True, host = '0.0.0.0', port = 5035)
