import ctypes
ctypes.windll.user32.SetProcessDPIAware()


import pygame
import math

pygame.init()
width = 1200
height = 850
screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)

radius = 5
g = 10

stopped = 0
missed = 0

running = True
screen.fill("black")

TIME_STAMP = 100 #no of frames
dt = 1/TIME_STAMP

MAX_BALLISTIC_MISSILE_VELOCITY = 120.0

defence_x,defence_y,defence_radius = 0,height,700
defence_missile_velocity = 50

ballisticMissiles = []
detectedMissiles = []
responseMissile = []


class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        for num in range(1, 6):
            img = pygame.image.load(f"exp{num}.png")
            img = pygame.transform.scale(img, (100, 100))
            self.images.append(img)
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.counter = 0

    def update(self):
        explosion_speed = 4
        # update explosion animation
        self.counter += 1

        if self.counter >= explosion_speed and self.index < len(self.images) - 1:
            self.counter = 0
            self.index += 1
            self.image = self.images[self.index]

        # if the animation is complete, reset animation index
        if self.index >= len(self.images) - 1 and self.counter >= explosion_speed:
            self.kill()

explosion_group = pygame.sprite.Group()


class BallisticMissile:
    def __init__(self,x,y,xt,color,v = MAX_BALLISTIC_MISSILE_VELOCITY):
        self.x = x
        self.y = y
        self.xt = xt #target is on ground
        range = self.x - self.xt #ballistic missile will be on right

        self.v = v
        self.thetha = 0.5*math.asin(range*g/(self.v**2))

        self.color = color
        self.vx = self.v*math.cos(self.thetha)
        self.vy = self.v*math.sin(self.thetha)
        self.paths = []

    def update(self):
        self.vy -= g*dt
        self.x -= self.vx*dt
        self.y -= self.vy*dt + 0.5*g*dt*dt

    def draw(self):
        global missed
        if 0 <= self.x < width and 0 <= self.y <= height:
            self.paths.append([self.x,self.y])
            for p in self.paths:
                pygame.draw.circle(screen,self.color, p, radius)
            pygame.draw.circle(screen,"white", [self.x,self.y], radius,5)

        else:
            missed += 1
            explosion = Explosion(self.x, self.y)
            explosion_group.add(explosion)
            if self in detectedMissiles:
                detectedMissiles.remove(self)
            if self in ballisticMissiles:
                ballisticMissiles.remove(self)


class DefenceMissile:
    def __init__(self,targetMissile : BallisticMissile,x=defence_x,y=defence_y,v=defence_missile_velocity,color = "blue"):
        self.targetMissile = targetMissile
        self.x = x
        self.y = y
        self.v = v
        self.color = color
        self.dx = targetMissile.x - self.x
        self.dy = targetMissile.y - self.y
        thetha = self.dy/self.dx
        self.vx = self.v*math.cos(thetha)
        self.vy = self.v*math.sin(thetha)
        self.path = []

    def distance(self,a,b):
        return math.sqrt((a[0]-b[0])**2+(a[1]-b[1])**2)


    def update(self):
        global stopped
        self.dx = self.targetMissile.x - self.x
        self.dy = self.targetMissile.y - self.y
        thetha = self.dy / self.dx
        if self.dx > 0:
            self.vx = self.v * math.cos(thetha)
            self.vy = self.v * math.sin(thetha)
            self.x += self.vx*dt
            self.y += self.vy*dt
        elif self.dx < 50:
            # missed
            self.vy -= g*dt
            self.x += self.vx*dt
            self.y += self.vy*dt
            responseMissile.remove(self)

        if self.distance([self.x,self.y],[self.targetMissile.x,self.targetMissile.y]) < 2*radius:
            if self.targetMissile in ballisticMissiles and self.targetMissile in detectedMissiles:
                explosion = Explosion(self.x,self.y)
                explosion_group.add(explosion)
                ballisticMissiles.remove(self.targetMissile)
                detectedMissiles.remove(self.targetMissile)
                if self in responseMissile:
                    responseMissile.remove(self)
                stopped += 1

    def draw(self):
        if 0 <= self.x < width and 0 <= self.y <= height:
            self.path.append([self.x, self.y])

            for p in self.path:
                # pygame.draw.circle(screen,self.color, p, radius,2)
                pygame.draw.circle(screen,"blue", p, radius)
            pygame.draw.circle(screen,"white", [self.x,self.y], radius,5)



# missile = BallisticMissile(900,800,0,"red")

class Radar:
    def __init__(self,x,y,radius):
        self.x = x
        self.y = y
        self.radius = radius

    def distance(self,missile):
        return math.sqrt((self.x-missile.x)**2+(self.y-missile.y)**2)

    def detect(self):
        d = []
        for m in ballisticMissiles:
            if self.distance(m) < self.radius and m not in detectedMissiles:
                d.append(m)
        return d


class DefenceSystem:
    def __init__(self,x=defence_x,y=defence_y,color="blue"):
        self.x = x
        self.y = y
        self.color = color

    def launchMissile(self,missile):
        # for m in :
        detectedMissiles.append(missile)
        responseMissile.append(DefenceMissile(missile,self.x,self.y,color=self.color))

    def update(self):
        for r in responseMissile:
            r.update()

    def draw(self):
        [r.draw() for r in responseMissile]


defense = DefenceSystem()

clock = pygame.time.Clock()


font = pygame.font.Font('freesansbold.ttf', 20)



while running:
    screen.fill("black")
    clock.tick(TIME_STAMP)
    m_text = font.render("missed : " + str(missed), True, "white", "black")
    s_text = font.render("stopped : " + str(stopped), True, "white", "black")
    m_textRect = m_text.get_rect()
    s_textRect = s_text.get_rect()
    m_textRect.center = (100, 50)
    s_textRect.center = (800, 50)
    screen.blit(m_text,m_textRect)
    screen.blit(s_text,s_textRect)

    explosion_group.draw(screen)
    explosion_group.update()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos

            if height >= pos[1] > height - 50:
            # if height >= pos[1]:
                ballisticMissiles.append(BallisticMissile(pos[0],pos[1],0,"red"))

    for m in ballisticMissiles:
        m.draw()
        m.update()

    detected = Radar(defence_x,defence_y,defence_radius).detect()
    if detected:
        for d in detected:
            defense.launchMissile(d)

    defense.draw()
    defense.update()


    pygame.display.flip()

pygame.quit()
