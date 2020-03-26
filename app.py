from flask import Flask, render_template, request
import json
import example

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

    """
    scenario = example.data
    with open("test_scenario.json", "w") as write_file:
        json.dump(scenario, write_file)
    """

    with open("test_scenario.json", "r") as read_file:
        scenario = json.load(read_file)
    return render_template('start.html', scenario=scenario)


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
    app.run(debug = True, host = '0.0.0.0', port = 5035)
