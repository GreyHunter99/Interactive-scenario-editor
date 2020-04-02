from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
import example

app = Flask(__name__)
app.secret_key = 'extra secret key'

scenarioList = {}


@app.route('/')
def menu():
    refreshScenarioList()
    session['playingScenario'] = False
    return render_template('menu.html')


@app.route('/list')
def list():
    global scenarioList

    return render_template('list.html', scenarioList=scenarioList)


@app.route('/start')
def start():
    global scenarioList

    #saveToDatabase("0.json", example.data)
    #session['scenario'] = loadFromDatabase("0.json")

    scenarioId = request.args.get('scenarioId')
    if scenarioId == None:
        return redirect(url_for('menu'))

    session['scenario'] = scenarioList[scenarioId]

    return render_template('start.html', scenario=session['scenario'])


@app.route('/scenario')
def question():
    questionId = request.args.get('questionId')

    if questionId == None:
        return redirect(url_for('menu'))

    if session['playingScenario'] == False:
        session['startingQuestionId'] = int(questionId)
        session['playingScenario'] = True

    return render_template('question.html', scenario=session['scenario'], questionId=questionId, startingQuestionId=session['startingQuestionId'])


@app.route('/createScenario')
def createScenario():
    global scenarioList

    return render_template('editScenario.html')


@app.route('/editScenario', methods=['GET', 'POST'])
def editScenario():
    scenarioId = request.args.get('scenarioId')

    if scenarioId != None:
        session['scenario'] = scenarioList[scenarioId]
    elif session['scenario'] == None:
        return redirect(url_for('menu'))

    if request.method == 'POST':
        session['scenario']['questions'][session['questionId']]['text'] = request.form['text']
        for key in session['scenario']['questions'][session['questionId']]['optionalText']:
            session['scenario']['questions'][session['questionId']]['optionalText'][key]['text'] = request.form['optionalText'+key]
            session['scenario']['questions'][session['questionId']]['optionalText'][key]['conditionalQuestionId'] = request.form['optionalTextConditionalQuestionId'+key]
        for key in session['scenario']['questions'][session['questionId']]['answers']:
            session['scenario']['questions'][session['questionId']]['answers'][key]['text'] = request.form['answerText'+key]
            session['scenario']['questions'][session['questionId']]['answers'][key]['questionId'] = request.form['answerQuestionId'+key]
            session['scenario']['questions'][session['questionId']]['answers'][key]['conditionalQuestionId'] = request.form['answerConditionalQuestionId'+key]

        scenario = {str(session['scenario']['id']) : session['scenario']}
        saveToDatabase(str(session['scenario']['id'])+'.json', scenario)

    return render_template('editScenario.html', scenario=session['scenario'])


@app.route('/edit')
def edit():
    questionId = request.args.get('questionId')

    if questionId != None:
        session['questionId'] = questionId
    else:
        return redirect(url_for('menu'))

    return render_template('edit.html', scenario=session['scenario'], questionId=questionId)


def updateQuestion():
    pass


def saveToDatabase(name, scenario):
    "Funkcja zapisująca scenariusz do bazy"
    with open("database/scenarios/"+name, "w") as write_file:
        json.dump(scenario, write_file)


def loadFromDatabase(name):
    "Funkcja wczytująca scenariusz z bazy"
    with open("database/scenarios/"+name, "r") as read_file:
        scenario = json.load(read_file)
    return scenario


def refreshScenarioList():
    "Funkcja aktualizująca listę scenariuszy"
    global scenarioList
    scenarioList = {}
    for scenario in os.listdir("database/scenarios/"):
        currentScenario = loadFromDatabase(scenario)
        scenarioList.update(currentScenario)


if __name__ == '__main__':
    app.run(debug = True, host = '0.0.0.0', port = 5035)
