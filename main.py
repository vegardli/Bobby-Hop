import pygame, time, sys, math
from pygame.locals import *

height = 0
width = 0

screen = 0

camera = [0,0]

levelList = ["l1.level", "l2.level", "l3.level"]
currentLevel = 0
score = 0
totalScore = 0

ticks = 0

# Keys
up = 0
down = 0
left = 0
right = 0

# Attributes
acc = 0.5
maxSpeed = 10
jmpSpeed = 10
attachLength = 200
attachRestLength = attachLength*(1.0/3.0)
attachStrength = 0.0005
damping = 0.98
gravity = 0.3
boostCoefficient = 3
boostDecay = 0.999
ejectionCoefficient = 0.1

class Drawable:
	def __init__(self, imgPath):
		self.image = pygame.image.load(imgPath)
		self.x = 0
		self.y = 0

	def draw(self):
		screen.blit(self.image, (self.x - camera[0], self.y - camera[1]))


class Player(Drawable):
	def __init__(self):
		Drawable.__init__(self, "player.png")
		self.xvel = 0
		self.yvel = 0

		self.onGround = True

		self.attached = False
		self.attachedTo = 0
		self.attachedBoost = 0
		self.attachedDirection = 0
		self.attachColor = [170, 20, 50]


	def update(self):
		if left and self.xvel > -maxSpeed:
			self.xvel -= acc

		if right and self.xvel < maxSpeed:
			self.xvel += acc

		# gravity
		self.yvel += gravity

		if self.y + self.yvel > 0:
			self.y = 0
			self.yvel = 0
			self.onGround = True

		if self.onGround and not left and not right:
			self.xvel *= 0.9

		# Check attach length
		if self.attached and findDistance(self, self.attachedTo) > attachLength:
			self.attached = False

		# Swings!
		if self.attached:
			dist = findDistance(self, self.attachedTo)
			self.yvel -= (self.y - self.attachedTo.y)*attachStrength*(dist-attachRestLength)
			self.xvel -= (self.x - self.attachedTo.x)*attachStrength*(dist-attachRestLength)

			if up and self.yvel > -maxSpeed:
				self.yvel -= acc
			if down and self.yvel < maxSpeed:
				self.yvel += acc

			newdir = findDirection(self, self.attachedTo)
			deltadir = self.attachedDirection - newdir
			if deltadir > math.pi:
				deltadir -= 2*math.pi
			elif deltadir < -math.pi:
				deltadir += 2*math.pi

			self.attachedBoost = max(min(self.attachedBoost + deltadir*boostCoefficient, 100), -100)

			self.attachedBoost *= boostDecay

			self.attachedDirection = newdir

			self.attachColor = [int(170-abs(self.attachedBoost)), 20, int(50+abs(self.attachedBoost)*2)]

		# Damping
		self.xvel *= damping
		self.yvel *= damping

		self.x += self.xvel
		self.y += self.yvel

	def attach(self, dot):
		self.attached = True
		self.attachedTo = dot
		self.attachedDirection = findDirection(self, dot)
		self.attachedBoost = 0

	def detach(self):
		self.attached = False

		self.xvel *= abs(self.attachedBoost)*ejectionCoefficient
		self.yvel *= abs(self.attachedBoost)*ejectionCoefficient

class Goal(Drawable):
	def __init__(self, x, y):
		Drawable.__init__(self, "goal.png")
		self.x = x
		self.y = y



class Dot(Drawable):
	def __init__(self, x, y):
		Drawable.__init__(self, "dot.png")
		self.image.set_colorkey((56, 56, 56))
		self.x = x
		self.y = y

def findDistance(drawable1, drawable2):
	return math.sqrt((drawable1.x-drawable2.x)**2 + (drawable1.y-drawable2.y)**2)

def findNearestDot(x,y):
	global objs

	nearestLength = sys.maxint
	nearest = None

	for i in range(len(objs)):
		if not isinstance(objs[i], Dot):
			continue

		length = (objs[i].x-x)**2 + (objs[i].y-y)**2
		if length < nearestLength:
			nearestLength = length
			nearest = objs[i]

	return nearest

def findDirection(o1, o2):
	return math.atan2(o1.y-o2.y, o1.x-o2.x)

def loadMap(filename):
	global objs,score

	score = 0

	fil = open(filename, "r")

	mapdata = fil.read().split("\n")

	for line in mapdata:
		if line == "":
			continue

		if len(line.split("=")) == 2:
			lhs = line.split("=")[0]
			rhs = line.split("=")[1]

			if lhs == "Dot":
				if len(rhs.split(",")) != 2:
					print("Error: Map load error")
					sys.exit()

				x = int(rhs.split(",")[0])
				y = int(rhs.split(",")[1])

				objs.append(Dot(x,y))

			elif lhs == "Goal":
				if len(rhs.split(",")) != 2:
					print("Error: Map load error")
					sys.exit()

				x = int(rhs.split(",")[0])
				y = int(rhs.split(",")[1])

				newGoal = Goal(x,y)
				objs.append(newGoal)
				goals.append(newGoal)

			elif lhs == "startScore":
				score = int(rhs)

			elif lhs == "levelHint":
				screen.fill((0,0,0))
				if len(rhs.split(",")) == 1:
					display_splash(rhs)

				else:
					display_splash(rhs.split(",")[0], rhs.split(",")[1])

				time.sleep(2)

	fil.close()

def unloadMap():
	global objs,goals,totalScore, score

	objs = [objs[0]]
	goals = []

	objs[0].x = 0
	objs[0].y = 0
	objs[0].xvel = 0
	objs[0].yvel = 0

	totalScore += score


def checkForFinish():
	global goals

	for obj in goals:
		if abs(obj.x+48 - objs[0].x) < 80 and abs(obj.y - objs[0].y) < 32:
			nextLevel()

def nextLevel():
	global currentLevel, levelList, score, totalScore, success

	currentLevel += 1

	unloadMap()

	if currentLevel+1 > len(levelList):
		display_splash("You won the game!", "Total score: " + str(totalScore))
		pygame.mixer.music.fadeout(5000)
		time.sleep(5)
		pygame.event.post(pygame.event.Event(QUIT))

	else:
		display_splash("Congratulations! Loading level " + str(currentLevel+1), "Level score: " + str(score))
		loadMap(levelList[currentLevel])

		pygame.mixer.music.set_volume(0.7)
		success.play()

		time.sleep(1)
		pygame.mixer.music.set_volume(1.0)


def display_splash(string, string2 = False):
	global font,font2
	
	print(string)

	text = font.render(string, 1, (255,255,255))
	(w,h) = text.get_size()
	screen.blit(text, (width/2 - w/2, height/2 - h/2))

	if string2 != False:
		text2 = font2.render(string2, 1, (200,200,200))
		(w2,h2) = text2.get_size()
		screen.blit(text2, (width/2 - w2/2, height/2 - h/2 + h2*2))

	pygame.display.flip()

def displayScore():
	global font3

	text = font3.render("Score: " + str(score), 1, (200,200,200))
	screen.blit(text, (0, 0))

if len(sys.argv) == 2:
	currentLevel = int(sys.argv[1])


objs = []
goals = []

pygame.init()
clock = pygame.time.Clock()
font = pygame.font.SysFont("monospace", 72)
font2 = pygame.font.SysFont("monospace", 48)
font3 = pygame.font.SysFont("monospace", 22)

# Music courtesy of Eric Skiff: http://ericskiff.com/music/
pygame.mixer.music.load("07 We're the Resistors.wav")
pygame.mixer.music.play(-1)

# Sound effect by grunz on Freesound: https://www.freesound.org/people/grunz/sounds/109663/
success = pygame.mixer.Sound("109663__grunz__success-low.wav")


vInfo = pygame.display.Info()
height = vInfo.current_h
width = vInfo.current_w

screen = pygame.display.set_mode((width, height), FULLSCREEN)

objs.append(Player())

loadMap(levelList[currentLevel])

while True:
	screen.fill((100,100,100))

	objs[0].update()

	checkForFinish()
	displayScore()

	camera[0] = objs[0].x - width/2
	camera[1] = objs[0].y - height/2

	# Draw ground
	pygame.draw.rect(screen, (170,20,50), (0, -camera[1] + 32, width, height))

	if objs[0].attached:
		pygame.draw.line(screen, objs[0].attachColor, (width/2 + 16, height/2 + 16), 
			(objs[0].attachedTo.x - camera[0] + 16, objs[0].attachedTo.y - camera[1] + 16), int(2+abs(objs[0].attachedBoost)*0.05))

	for obj in objs:
		obj.draw()

	for event in pygame.event.get():
		if event.type == QUIT:
			pygame.quit()
			sys.exit()

		elif event.type == KEYDOWN:
			if event.key == K_ESCAPE:
				pygame.event.post(pygame.event.Event(QUIT))

			if event.key == K_w:
				up = 1
				if objs[0].onGround:
					objs[0].yvel = -jmpSpeed
					objs[0].onGround = False

			elif event.key == K_a:
				left = 1

			elif event.key == K_s:
				down = 1

			elif event.key == K_d:
				right = 1

			elif event.key == K_SPACE:
				if objs[0].attached:
					objs[0].detach()

				else:
					dot = findNearestDot(objs[0].x, objs[0].y)
					if dot != None and findDistance(dot, objs[0]) < attachLength:
						objs[0].attach(dot)

		elif event.type == KEYUP:
			if event.key == K_w:
				up = 0

			elif event.key == K_a:
				left = 0

			elif event.key == K_s:
				down = 0

			elif event.key == K_d:
				right = 0

	ticks += 1
	if ticks % 10 == 0:
		score = max(score-1, 0)

	pygame.display.flip()
	clock.tick(60)
