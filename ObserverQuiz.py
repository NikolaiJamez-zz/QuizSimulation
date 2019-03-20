import urllib.request
import json
import html
import random
import threading
import time
QUESTION_NUM = 10   # API Limits to 50 questions
QUESTION_INDEX = 0
ANSWER_INDEX = 1
TIME_LIMIT = 20
URL = "https://opentdb.com/api.php?amount={}&type=multiple".format(QUESTION_NUM)
NAME_LOCATION = "RandomNames.txt"  # Gets random contestant names from file
PLAYERS = 5
SEPARATOR = "=========="

# Creates the single quiz-master, chosen number of players with random names,
# questions to be read and plays as many rounds as there are questions
class Simulation:
    def __init__(self):
        self.q = Question()
        self.qm = QuizMaster(self.q)
        names = self.get_names()
        self.p = []
        for player in range(PLAYERS):
            self.p.append(Player(self.qm, names.pop()))

        while self.q.get_questions_left() > 0:
            self.play_round()
        self.display_winner()

    # Gets names from file and shuffles
    @staticmethod
    def get_names():
        file = open(NAME_LOCATION, "r")
        names = []
        for line in file.readlines():
            names.append(line[:-1])
        random.shuffle(names)
        file.close()
        return names

    # Controls everything needed to play a round including:
    # Forming a question and displaying it to the contestants
    # Create a thread for each contestant so they can "think" at different times
    # Display the contestants that got the answer correct 
    def play_round(self):
        self.qm.form_question()
        self.qm.display_question(self.qm.question, self.qm.all_answers)
        self.qm.give_question(self.qm.all_answers)
        for thread in self.qm.threads:
            thread.join()
        print("{} All players have answered {}".format(SEPARATOR, SEPARATOR))
        self.qm.display_winners()

    # Sorts tghrough all the winners and displays them in order of first to last
    def display_winner(self):
        winners = [self.p[0]]
        first = True
        for player in self.p:
            if not first:
                if player.wins > winners[0].wins:
                    winners.clear()
                    winners.append(player)
                elif player.wins == winners[0].wins:
                    winners.append(player)
            first = False
        print("{} GAME OVER {}\nThese players are your winners!\n{}".format(SEPARATOR * 5, SEPARATOR * 5, SEPARATOR))
        for player in winners:
            time.sleep(2)
            print(player.name)
        print(SEPARATOR * 10)

# thread used to allow contestants to "think" at different speeds
class DecideThread(threading.Thread):
    def __init__(self, p, a):
        threading.Thread.__init__(self)
        self.player = p
        self.a = a

    def run(self):
        time.sleep(random.randrange(2, TIME_LIMIT))
        print("{} has answered".format(self.player.name))
        self.player.choose_answer(self.a)


# Handles getting and making the question readbale
class Question:
    def __init__(self):
        self.questions = []
        self.make_questions()
    # Gets questions from Open Trivia DB and sorts them into an array
    def make_questions(self):
        self.questions.clear()
        r = urllib.request.urlopen(URL)
        source = r.read()
        data = json.loads(source)
        data = data['results']
        for question_num in range(QUESTION_NUM):
            question_string = html.unescape(data[question_num]['question'])
            all_answers = html.unescape(data[question_num]['incorrect_answers'])
            all_answers.insert(0, html.unescape(data[question_num]['correct_answer']))
            self.questions.append([question_string, all_answers])
        random.shuffle(self.questions)

    def get_question(self):
        return self.questions.pop()

    def get_questions_left(self):
        return len(self.questions)


# Handles everything a contestant needs to play
class Player:
    def __init__(self, quiz_master, name):
        self.quiz_master = quiz_master
        self.name = name
        quiz_master.register_observer(self)
        self.answer = ""
        self.wins = 0

    # Send answer to quiz master
    def choose_answer(self, a):
        self.quiz_master.receive_answer(a[random.randrange(len(a))], self)


# Handles everything the quiz master needs to run the game
class QuizMaster:
    def __init__(self, q):
        self.players = []
        self.q = q
        self.answers = []
        self.question = ""
        self.answer = ""
        self.all_answers = []
        self.threads = []

    # Registers a player
    def register_observer(self, o):
        self.players.append(o)

    # Forms the question and answers
    def form_question(self):
        self.answers.clear()
        data = self.q.get_question()
        self.question = data[QUESTION_INDEX]
        self.all_answers = data[ANSWER_INDEX]
        self.answer = data[1][0]

    # Displays question to contestants
    def display_question(self, q, a):
        print("{}\nQuestion {}\n{}\n{}\n[1] {}    [2] {}    [3] {}    [4] {}\n{}".format(SEPARATOR * 10, QUESTION_NUM - self.q.get_questions_left(), SEPARATOR, q, a[0], a[1], a[2], a[3], SEPARATOR))

    # Gives each player a thread and provides them with the question/answers
    def give_question(self, a):
        self.threads.clear()
        for player in range(PLAYERS):
            self.threads.append(DecideThread(self.players[player], a))
            self.threads[player].start()

    # Recieves answer from contestant
    def receive_answer(self, a, player):
        self.answers.append([a, player])

    # Displays who was correct and the answer
    def display_winners(self):
        for answer in self.answers:
            if answer[0] == self.answer:
                print("{} was correct".format(answer[1].name))
                answer[1].wins += 1
        print("The answer was {}".format(self.answer))
        time.sleep(5)

    def remove_observers(self):
        self.observers.clear()

# Starts simulation
s = Simulation()
