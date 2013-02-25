import pygame
import random
import time
import math
import sys
import os

__screenResolution = [800,600]
__fullscreenValue = False

def makeFont(size):
    return pygame.font.Font("freesansbold.ttf", size)

def getResolution():
    global __screenResolution
    width, height = __screenResolution
    return (width, height)

def isFullscreen():
    global __fullscreenValue
    return __fullscreenValue

def loadGraphicsSettings():
    global __screenResolution
    global __fullscreenValue
    settings = INIFile("settings.ini")
    settings.readonly = False # generate new file if needed
    if not settings.hasValue("graphics", "width"):
        settings.makeValue("graphics", "width", 800)
    if not settings.hasValue("graphics", "height"):
        settings.makeValue("graphics", "height", 600)
    if not settings.hasValue("graphics", "fullscreen"):
        settings.makeValue("graphics", "fullscreen", "False")
    width = int(settings.getValue("graphics","width"))
    height = int(settings.getValue("graphics","height"))
    __screenResolution = (width, height)
    if settings.getValue("graphics","fullscreen") == "True":
        __fullscreenValue = True
    else:
        __fullscreenValue = False
    settings.save()

class INIFile():
    def __init__(self, filename, readonly = False):
        self.sections = {}
        self.filename = filename
        self.readonly = readonly
        if not self.load():
            print "error loading '%s'" % filename
    def __del__(self):
        self.save()
    def hasSection(self, name):
        return (name in self.sections.iterkeys())
    def hasValue(self, section, name):
        if not self.hasSection(section): return False
        return (name in self.sections[section].iterkeys())
    def getValue(self, section, name):
        if not self.hasValue(section, name):
            return None
        return self.sections[section][name]
    def makeValue(self, section, name, value = None):
        if not self.hasSection(section):
            self.sections[section] = {}
        self.sections[section][name] = value
    def load(self):
        storeReadOnly = self.readonly
        self.readonly = True # if loading breaks, don't save
        f = None
        try:
            f = open(self.filename, "r")
        except:
            return False # error here
        lines = f.read().split("\n")
        for x in range(len(lines)):
            if lines[x].find("#") != -1:
                lines[x] = lines[x][:lines[x].find("#")]
            lines[x] = lines[x].strip()
        tempLines = lines
        lines = []
        for line in tempLines:
            if line: lines.append(line)
        currentSection = None
        for line in lines:
            if line.find("[") == 0:
                if line.find("]") == -1:
                    return False # error here
                currentSection = line[1:line.find("]")]
                self.sections[currentSection] = {}
            elif line.find("=") != -1:
                parts = line.split("=")
                name, value = parts[0], "=".join(parts[1:]) # just in case '=' is used in the value somewhere :S
                if currentSection is None:
                    return False # error here
                self.sections[currentSection][name] = value
            else:
                pass # error? no error? :S
        self.readonly = storeReadOnly
        return True
    def save(self):
        if self.readonly: return False
        f = None
        try:
            f = open(self.filename, "w")
        except:
            return False # error here
        for name, values in self.sections.iteritems():
            f.write("[%s]\n" % name)
            for valName, value in values.iteritems():
                f.write("%s=%s\n" % (valName, value))
        return True

class Vec2D:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def getX(self):
        return self.x
    def getY(self):
        return self.y
    def get(self):
        return (self.x, self.y)
    def getInt(self):
        return (int(self.x), int(self.y))

class Entity:
    def __init__(self, pos):
        self.removeMe = False
        self.renderBounds = ((-1,-1),(1,1))
        self.pos = pos
        self.friction = 1.0
        self.actuallyClip = True
        self.clipTo = None
        self.wrapAround = False
        self.vel = Vec2D(0,0)
    def setClipValues(self, topLeft, bottomRight, wrapAround = False, actuallyClip = True):
        self.clipTo = (topLeft, bottomRight)
        self.wrapAround = wrapAround
        self.actuallyClip = actuallyClip
    def render(self, dest):
        pass
    def think(self, others, context):
        pass
    def notify(self, event):
        pass
    def onScreen(self, topLeft, bottomRight):
        if self.renderBounds is None: return True
        x, y = self.pos.get()
        x1, y1 = x + self.renderBounds[0][0], y + self.renderBounds[0][1]
        x2, y2 = x + self.renderBounds[1][0], y + self.renderBounds[1][1]
        lx, ly = topLeft
        rx, ry = bottomRight
        if (x1 >= lx and x1 <= rx) or (x2 >= lx and x2 <= rx):
            if (y1 >= ly and y1 <= ry) or (y2 >= ly and y2 <= ry):
                return True
        return False
    def move(self):
        mX, mY = self.vel.get()
        newX = self.pos.getX() + mX
        newY = self.pos.getY() + mY
        if self.clipTo is not None and self.actuallyClip:
            if self.wrapAround:
                if newX < self.clipTo[0][0]:
                    newX = self.clipTo[1][0]
                elif newX > self.clipTo[1][0]:
                    newX = self.clipTo[0][0]
                if newY < self.clipTo[0][1]:
                    newY = self.clipTo[1][1]
                elif newY > self.clipTo[1][1]:
                    newY = self.clipTo[0][1]
            else:
                if newX < self.clipTo[0][0]:
                    newX = self.clipTo[0][0]
                elif newX > self.clipTo[1][0]:
                    newX = self.clipTo[1][0]
                if newY < self.clipTo[0][1]:
                    newY = self.clipTo[0][1]
                elif newY > self.clipTo[1][1]:
                    newY = self.clipTo[1][1]
        self.pos = Vec2D(newX, newY)
        self.vel = Vec2D(mX * self.friction, mY * self.friction)

class EntitySpawner(Entity):
    def __init__(self, pos, factory, delayRange, maximum):
        Entity.__init__(self, pos)
        self.made = []
        self.maximum = maximum
        self.factory = factory
        self.delay = delayRange
        self.nextDelay = random.randint(self.delay[0], self.delay[1]) / 1000.0
        self.last = time.clock()
        self.renderBounds = None
    def spawn(self):
        make = self.factory.make(self)
        self.made.append(make)
        return make
    def think(self, others, context):
        self.factory.think(others, context)
        if time.clock() >= self.last + self.nextDelay and len(self.made) < self.maximum:
            others.append(self.spawn())
            self.nextDelay = random.randint(self.delay[0], self.delay[1]) / 1000.0
            self.last = time.clock()
        toRemove = []
        for each in self.made:
            if each.removeMe:
                toRemove.append(each)
        for each in toRemove:
            self.made.remove(each)
    def render(self, dest):
        self.factory.render(dest)

class DebugEntity(Entity):
    def __init__(self, pos):
        Entity.__init__(self, pos)
        self.renderBounds = None
    def render(self, dest):
        pygame.draw.rect(dest, (255,0,255), (self.pos.get(), (32,32)))

class Asteroid(Entity):
    def __init__(self, pos, size, bearing, theEmitter):
        Entity.__init__(self, pos)
        self.theEmitter = theEmitter
        self.maxSize = size
        self.size = size
        self.speed = 0.5
        mx = math.cos(bearing) * self.speed
        my = math.sin(bearing) * self.speed
        self.vel = Vec2D(mx, my)
        self.renderBounds = ((-self.size,-self.size), (self.size, self.size))
    def dead(self):
        isDead = (self.size < 8)
        if isDead: self.removeMe = True
        return isDead
    def getShot(self):
        partCount = random.randint(5,20)
        for x in range(partCount):
            myX, myY = self.pos.get()
            self.theEmitter.pos = Vec2D(myX, myY)
            theAngle = random.randint(1,360)*math.pi/180
            thePower = random.randint(50,100)/10.0
            self.theEmitter.setDirection(theAngle, thePower)
            self.theEmitter.emit()
        self.size = self.size / 2
        self.renderBounds = ((-self.size,-self.size), (self.size, self.size))
        return self.dead()
    def render(self, dest):
        pygame.draw.circle(dest, (50,50,50), self.pos.getInt(), self.size)

class AsteroidFactory(Entity):
    def __init__(self, thePlayer):
        self.player = thePlayer
        self.asteroidSize = 32
        self.emitter = ParticleEmitter(Vec2D(0,0), 200, None, [1,6], [200,700], [(50,50,50),(100,100,100),(255,128,0)])
    def make(self, spawner):
        width, height = getResolution()
        px, py = self.player.pos.get()
        someAngle = random.randint(1,360) * math.pi / 180.0
        distance = 4000.0 # extreme
        px += math.cos(someAngle) * distance
        py += math.sin(someAngle) * distance
        newAsteroid = Asteroid(Vec2D(px,py), self.asteroidSize, random.randint(0,359) * math.pi / 180.0, self.emitter)
        newAsteroid.setClipValues((-self.asteroidSize,-self.asteroidSize),(width+self.asteroidSize,height+self.asteroidSize),True)
        newAsteroid.move()
        return newAsteroid
    def think(self, others, context):
        self.emitter.think(others, context)
    def render(self, dest):
        self.emitter.render(dest)

class Particle(Entity):
    def __init__(self, pos, vel, col, size, lifetime):
        Entity.__init__(self, pos)
        self.col = col
        self.vel = vel
        self.size = size
        self.renderBounds = ((-self.size,-self.size),(self.size,self.size))
        self.life = lifetime
        self.friction = 0.999
        self.start = time.clock()
    def dead(self):
        return (time.clock() > self.start + self.life)
    def render(self, dest):
        pygame.draw.circle(dest, self.col, self.pos.getInt(), int(self.size))

class ParticleEmitter(Entity):
    def __init__(self, pos, maxPop, delayRange, sizeRange, lifeRange, colours):
        self.maxParticles = maxPop
        self.delayRange = delayRange
        self.sizeRange = sizeRange
        self.lifeRange = lifeRange
        self.renderBounds = None
        self.cols = colours
        self.pos = pos
        self.particles = []
        self.last = time.clock()
        if self.delayRange is None:
            self.nextDelay = None
        else:
            self.nextDelay = random.randint(delayRange[0], delayRange[1]) / 1000.0
    def emit(self):
        if len(self.particles) >= self.maxParticles:
            return
        nextCol = random.choice(self.cols)
        nextSize = random.randint(self.sizeRange[0], self.sizeRange[1])
        nextLife = random.randint(self.lifeRange[0], self.lifeRange[1])
        nextLife = nextLife/1000.0
        nextPos = Vec2D(self.pos.getX(), self.pos.getY())
        nextVel = Vec2D(self.vel.getX(), self.vel.getY())
        particle = Particle(nextPos, nextVel, nextCol, nextSize, nextLife)
        self.particles.append(particle)
        self.last = time.clock()
        if self.nextDelay is not None:
            self.nextDelay = random.randint(self.delayRange[0],\
                                            self.delayRange[1]) / 1000.0
    def setDirection(self, angle, power):
        mx = math.cos(angle) * power
        my = math.sin(angle) * power
        self.vel = Vec2D(mx,my)
    def think(self, others, context):
        toRemove = []
        if self.nextDelay is not None:
            if time.clock() > self.last + self.nextDelay:
                self.emit()
        for particle in self.particles:
            if particle.dead() and particle not in toRemove:
                toRemove.append(particle)
                continue
            particle.move()
        for bad in toRemove:
            self.particles.remove(bad)
    def render(self, dest):
        for part in self.particles:
            part.render(dest)

class MultiplierGraphic(Entity):
    def __init__(self, pos, multiplier, size = 14):
        Entity.__init__(self, pos)
        self.lifeSpan = 2000.0
        self.bornTime = time.clock()
        self.multiplier = multiplier
        self.fontSize = size
        tempFont = makeFont(self.fontSize)
        self.rendered = tempFont.render("x%s" % self.multiplier, True, (0,255,0))
        self.renderBounds = ((-1,-1), self.rendered.get_size())
        angle = random.randint(1,360) * math.pi / 180.0
        speed = random.randint(5,15) / 10.0
        mx, my = math.cos(angle) * speed, math.sin(angle) * speed
        self.vel = Vec2D(mx, my)
    def think(self, others, context):
        if time.clock() >= self.bornTime + (self.lifeSpan / 1000.0):
            self.removeMe = True
    def render(self, dest):
        dest.blit(self.rendered, (self.pos.get(), (0,0)))

class Bullet(Entity):
    def __init__(self, pos, size, bearing, speed, thePlayer):
        Entity.__init__(self, pos)
        self.emitter = ParticleEmitter(self.pos, 200, [20,100], [1,2], [10,200], [(0,0,255), (50,50,255), (100,100,255)])
        self.thePlayer = thePlayer
        self.bearing = bearing
        self.size = size
        self.timeBorn = time.clock()
        self.lifespan = 1500 / 1000.0 # ms, divide by 1000.0 to get seconds
        self.renderBounds = ((-self.size,-self.size), (self.size, self.size))
        mx, my = math.cos(bearing) * speed, math.sin(bearing) * speed
        self.vel = Vec2D(mx, my)
    def collisionCheck(self, others):
        for index in range(len(others)):
            x = others[index]
            if x is self: continue
            if not isinstance(x, Asteroid): continue
            mx, my = self.pos.get()
            ox, oy = x.pos.get()
            dx, dy = mx-ox, my-oy
            distance = math.sqrt((dx*dx)+(dy*dy))
            if distance <= self.size + x.size:
                if time.clock() < self.thePlayer.spreeStart + (self.thePlayer.spreeTime / 1000.0):
                    if self.thePlayer.scoreMultiplier < 10:
                        self.thePlayer.scoreMultiplier += 1
                    multiX, multiY = self.thePlayer.pos.get()
                    others.append(MultiplierGraphic(Vec2D(multiX, multiY), self.thePlayer.scoreMultiplier))
                else:
                    self.thePlayer.scoreMultiplier = 1.0 # score multiplier back to zero after the spree
                self.thePlayer.spreeStart = time.clock()
                self.thePlayer.score += ((x.maxSize - x.size) + 1) * self.thePlayer.scoreMultiplier
                itDied = x.getShot()
                newBearing = random.randint(1,360) * math.pi / 180
                px, py = x.pos.get()
                if itDied == False:
                    newAsteroid = Asteroid(Vec2D(px,py), x.size, newBearing, x.theEmitter)
                    newBearing += math.pi
                    mx, my = math.cos(newBearing) * x.speed, math.sin(newBearing) * x.speed
                    x.vel = Vec2D(mx, my)
                    others.append(newAsteroid)
                self.removeMe = True
                break
            others[index] = x
    def think(self, others, context):
        if time.clock() >= self.timeBorn + self.lifespan:
            self.removeMe = True
            return
        self.emitter.pos = self.pos
        newBearing = (self.bearing + 180) * math.pi / 180
        self.emitter.setDirection(newBearing, 1)
        self.emitter.think(None, context)
        self.collisionCheck(others)
    def render(self, dest):
        self.emitter.render(dest)
        pygame.draw.circle(dest, (60,60,255), self.pos.getInt(), self.size)

class PlayerModifier(Entity):
    def __init__(self, thePlayer):
        self.player = thePlayer
    def initialiseMod(self):
        pass
    def upgrade(self):
        return None
    def render(self, dest):
        pass
    def think(self, others, context):
        pass
    def notify(self, event):
        pass

class ImprovedEngineModifier(PlayerModifier):
    def __init__(self, thePlayer):
        PlayerModifier.__init__(self, thePlayer)
    def initialiseMod(self):
        self.player.fuelCost /= 1.1
    def upgrade(self):
        return self

class AutomaticGunModifier(PlayerModifier):
    def __init__(self, thePlayer):
        PlayerModifier.__init__(self, thePlayer)
    def initialiseMod(self):
        self.player.automatic = True

class RapidFireModifier(PlayerModifier):
    def __init__(self, thePlayer):
        PlayerModifier.__init__(self, thePlayer)
    def initialiseMod(self):
        self.player.shotDelay -= 100
    def upgrade(self):
        return self

class LaserSightModifier(PlayerModifier):
    def __init__(self, thePlayer):
        PlayerModifier.__init__(self, thePlayer)
        self.nextLevel = LaserSightModifierLevel2(thePlayer)
    def render(self, dest):
        ex = self.player.pos.x + math.cos(self.player.bearing) * 1000.0
        ey = self.player.pos.y + math.sin(self.player.bearing) * 1000.0
        pygame.draw.line(dest, (255,0,0), self.player.pos.get(), (ex, ey))
    def upgrade(self):
        return self.nextLevel

class LaserSightModifierLevel2(PlayerModifier):
    def __init__(self, thePlayer):
        PlayerModifier.__init__(self, thePlayer)
    def render(self, dest):
        mx, my = self.player.vel.get()
        bx = mx + math.cos(self.player.bearing) * self.player.bulletSpeed
        by = my + math.sin(self.player.bearing) * self.player.bulletSpeed
        dx, dy = self.player.pos.get()
        for x in range(100):
            pygame.draw.circle(dest, (255,0,0), (dx,dy), 2)
            scaleFactor = 2
            dx += (bx * scaleFactor)
            dy += (by * scaleFactor)

class LargerBulletModifier(PlayerModifier):
    def __init__(self, thePlayer):
        PlayerModifier.__init__(self, thePlayer)
    def initialiseMod(self):
        self.player.bulletSize += 1
    def upgrade(self):
        return self

class AutoEvasionModifier(PlayerModifier):
    def __init__(self, thePlayer):
        PlayerModifier.__init__(self, thePlayer)
        self.panicDistance = 200.0
        self.force = 50.0
    def think(self, others, context):
        for x in range(len(others)):
            entity = others[x]
            if entity is self: continue
            if not isinstance(entity, Asteroid): continue
            mx, my = self.player.pos.get()
            ox, oy = entity.pos.get()
            dx, dy = mx-ox, my-oy
            distance = math.sqrt((dx*dx)+(dy*dy))
            if distance < self.panicDistance:
                angle = math.atan2(dy, dx)
                finalMultiplier = (1 / distance ** 2) * self.force
                self.player.vel.x += math.cos(angle) * finalMultiplier
                self.player.vel.y += math.sin(angle) * finalMultiplier
                self.player.score -= finalMultiplier

class Control(Entity):
    def __init__(self, pos, size):
        Entity.__init__(self, pos)
        self.pos = pos
        self.size = size
    def render(self, dest):
        pass
    def think(self, others, context):
        pass
    def notify(self, event):
        pass

class GroupControl(Control):
    def __init__(self, pos, contains = []):
        Control.__init__(self, pos, Vec2D(0,0))
        self.controls = contains
    def think(self, others, context):
        for control in self.controls:
            control.think(others, context)
    def render(self, dest):
        for control in self.controls:
            control.render(dest)
    def notify(self, event):
        for control in self.controls:
            control.notify(event)
    def add(self, control):
        self.controls.append(control)
        x, y = control.pos.get()
        control.pos = Vec2D(x + self.pos.x, y + self.pos.y)
    def changePos(self, newPos):
        nx, ny = newPos.get()
        ox, oy = self.pos.get()
        for control in self.controls:
            cx, cy = control.pos.get()
            control.pos = Vec2D(cx - ox + nx, cy - oy + ny)
        self.pos = Vec2D(nx, ny)

class GUI(GroupControl):
    def __init__(self):
        GroupControl.__init__(self, Vec2D(0,0), [])
        self.active = True
    def setActive(self, active):
        self.active = active
    def think(self, others, context):
        if self.active:
            GroupControl.think(self, others, context)
    def render(self, dest):
        if self.active:
            GroupControl.render(self, dest)
    def notify(self, event):
        if self.active:
            GroupControl.notify(self, event)

class Panel(GroupControl):
    def __init__(self, pos, size, colour, contains):
        GroupControl.__init__(self, pos, contains)
        self.size = size
        self.colour = colour
    def render(self, dest):
        pygame.draw.rect(dest, self.colour, (self.pos.get(), self.size.get()))
        GroupControl.render(self, dest)

class ToastPopup(Control):
    def __init__(self, pos, text, bgCol, fontCol, fontSize = 12):
        Control.__init__(self, pos, Vec2D(0,0))
        self.parent = None
        self.text = text
        self.bgCol = bgCol
        tempFont = makeFont(fontSize)
        self.renderText = tempFont.render(self.text, True, fontCol)
        width, height = self.renderText.get_size()
        self.size = Vec2D(width + 20, height + 20)
        self.renderBounds = ((0,0),self.size.get())
        self.destPos = None
        self.speed = None
        self.snapDist = 0.5
        self.lifeSpanWhenStopped = None
        self.lifeSpan = None
        self.timeBorn = time.clock()
    def __del__(self):
        if self.parent is not None:
            self.parent.toastCount -= 1
    def setLife(self, life, reset = True):
        self.lifeSpan = life
        if reset:
            self.timeBorn = time.clock()
    def setTranslation(self, dest, newSpeed, newLifeSpanWhenStopped = None):
        self.lifeSpanWhenStopped = newLifeSpanWhenStopped
        if dest is not None:
            destX, destY = dest
            self.destPos = (float(destX), float(destY))
        else: self.destPos = None
        if newSpeed is not None:
            self.speed = float(newSpeed)
        else: self.speed = None
    def think(self, others, context):
        if self.lifeSpan is not None:
            if time.clock() >= self.timeBorn + (self.lifeSpan / 1000.0):
                self.removeMe = True
        if self.destPos is not None and self.speed is not None:
            cx, cy = self.pos.get()
            tx, ty = self.destPos
            dx, dy = cx-tx, cy-ty
            distance = math.sqrt((dx**2)+(dy**2))
            if distance == 0: return
            if distance < self.snapDist:
                self.pos = Vec2D(tx, ty)
                return
            angle = math.atan2(dy, dx)
            angle += math.pi
            mx = math.cos(angle) * self.speed
            my = math.sin(angle) * self.speed
            self.pos = Vec2D(cx + mx, cy + my)
            cx, cy = self.pos.get()
            dx, dy = cx-tx, cy-ty
            distance = math.sqrt((dx**2)+(dy**2))
            if distance < self.snapDist:
                self.pos = Vec2D(tx, ty)
                self.setLife(self.lifeSpanWhenStopped)
    def render(self, dest):
        pygame.draw.rect(dest, self.bgCol, (self.pos.get(), self.size.get()))
        x, y = self.pos.get()
        dest.blit(self.renderText, (x+10,y+10,0,0))

class ToastManager(Control):
    def __init__(self, toastCount, bgCol, txtCol, lifeSpan, startPos, direction, speed):
        Control.__init__(self, startPos, Vec2D(0,0))
        self.maxToast = toastCount
        self.toastCount = 0
        self.bgCol = bgCol
        self.txtCol = txtCol
        self.lifeSpan = lifeSpan
        self.startPos = startPos
        self.dir = direction
        self.fontSize = 12
        self.speed = speed
        self.renderBounds = None
        self.newToasts = []
    def popup(self, text):
        if self.toastCount >= self.maxToast: return False
        newX, newY = self.pos.get()
        newToast = ToastPopup(Vec2D(newX, newY), text, self.bgCol, self.txtCol, self.fontSize)
        destX, destY = newX, newY
        renderW, renderH = newToast.size.get()
        destX += (self.toastCount + 1) * self.dir[0] * renderW
        destY += (self.toastCount + 1) * self.dir[1] * renderH
        newToast.setTranslation((destX, destY), self.speed, self.lifeSpan)
        newToast.parent = self
        self.newToasts.append(newToast)
        self.toastCount += 1
        return True
    def think(self, others, context):
        for toast in self.newToasts:
            others.append(toast)
        self.newToasts = []
    up = (0,-1)
    right = (1,0)
    down = (0,1)
    left = (-1,0)

class Button(Control):
    def __init__(self, pos, size, colour, depressedColour, text, textColour, callBack, argument):
        Control.__init__(self, pos, size)
        self.pressed = False
        self.col = colour
        self.enabled = True
        self.dpCol = depressedColour
        self.text = text
        self.font = makeFont(10)
        self.txtCol = textColour
        self.hook = callBack
        self.arg = argument
    def render(self, dest):
        colour = self.col
        if self.pressed: colour = self.dpCol
        if not self.enabled: colour = (50,50,50)
        pygame.draw.rect(dest, colour, (self.pos.get(), self.size.get()))
        textColour = self.txtCol
        if not self.enabled: textColour = (100,100,100)
        renderedText = self.font.render(self.text, True, self.txtCol)
        x, y = self.pos.get()
        rw, rh = renderedText.get_size()
        dx = x + (self.size.x - rw) / 2
        dy = y + (self.size.y - rh) / 2
        dest.blit(renderedText, ((dx,dy,0,0)))
    def notify(self, event):
        if not self.enabled: return
        if not self.pressed:
            if event.type != pygame.MOUSEBUTTONDOWN:
                return
            mx, my = event.pos
            lx, ly = self.pos.get()
            rx, ry = lx + self.size.x, ly + self.size.y
            if mx >= lx and mx <= rx and my >= ly and my <= ry:
                self.pressed = True
            else:
                self.pressed = False
        else:
            if event.type != pygame.MOUSEBUTTONUP:
                return
            mx, my = event.pos
            lx, ly = self.pos.get()
            rx, ry = lx + self.size.x, ly + self.size.y
            self.pressed = False
            if mx >= lx and mx <= rx and my >= ly and my <= ry:
                if self.hook is not None:
                    self.hook(self.arg)

class PopupMessageBase(Control):
    def __init__(self, message, col, txtCol, fontSize = 10):
        Control.__init__(self, Vec2D(0,0), Vec2D(0,0))
        self.msg = message
        self.col = col
        self.active = False
        self.txtCol = txtCol
        font = makeFont(fontSize)
        self.msgRender = font.render(self.msg, True, self.txtCol)
        width, height = getResolution()
        renderW, renderH = self.msgRender.get_size()
        self.pos = Vec2D((width-renderW)/2 - 10,(height-renderH)/2 - 10)
        self.size = Vec2D(renderW + 20, renderH + 20)
        self.buttons = []
        self.returnValue = None
    def activate(self, others, context):
        self.active = True
        self.returnValue = None
        self.think(others, context)
        return self.returnValue
    def notify(self, event):
        for button in self.buttons:
            button.notify(event)
    def think(self, others, context):
        fpsLimit = pygame.time.Clock()
        background = pygame.Surface(context.screen.get_size())
        background.blit(context.screen, (0,0,0,0))
        while self.active:
            fpsLimit.tick(30)
            for event in pygame.event.get():
                self.notify(event)
            for button in self.buttons:
                button.think(others, context)
            context.screen.blit(background, (0,0,0,0))
            self.render(context.screen)
            pygame.display.flip()
    def render(self, dest):
        if self.active:
            pygame.draw.rect(dest, self.col, (self.pos.get(), self.size.get()))
            x, y = self.pos.get()
            dest.blit(self.msgRender, ((x+10,y+10), (0,0)))
            for button in self.buttons:
                button.render(dest)

class PopupMessageOK(PopupMessageBase):
    def __init__(self, message, col, txtCol, fontSize = 10):
        PopupMessageBase.__init__(self, message, col, txtCol, fontSize)
        bx, by = self.pos.get()
        bx += 10
        by += 10
        r,g,b = self.col
        renderW, renderH = self.msgRender.get_size()
        self.okButton = Button(Vec2D(bx+renderW/2-30, by+renderH), Vec2D(60,20), self.col, (r-10,g-10,b-10), "OK", self.txtCol, self.okPressed, self)
        self.buttons.append(self.okButton)
        self.size.y += 20
    def okPressed(button, self):
        self.active = False
        self.returnValue = True
    def notify(self, event):
        PopupMessageBase.notify(self, event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.okPressed(self)

class PopupMessageYesNo(PopupMessageBase):
    def __init__(self, message, col, txtCol):
        PopupMessageBase.__init__(self, message, col, txtCol)
        bx, by = self.pos.get()
        bx += 10
        by += 10
        r,g,b = self.col
        renderW, renderH = self.msgRender.get_size()
        self.yesButton = Button(Vec2D(bx+renderW/2-65, by+20), Vec2D(60,20), self.col, (r-10,g-10,b-10), "YES", self.txtCol, self.yesPressed, self)
        self.noButton = Button(Vec2D(bx+renderW/2+5, by+20), Vec2D(60,20), self.col, (r-10,g-10,b-10), "NO", self.txtCol, self.noPressed, self)
        self.size.y += 20
        self.buttons = [self.yesButton, self.noButton]
    def yesPressed(button, self):
        self.active = False
        self.returnValue = True
    def noPressed(button, self):
        self.active = False
        self.returnValue = False

class UpgradeShop(Entity):
    def __init__(self, thePlayer):
        Entity.__init__(self, Vec2D(0,0))
        self.player = thePlayer
        self.gui = GUI()
        width, height = getResolution()
        self.closeShopButton = Button(Vec2D(5,5),Vec2D(100,20),(50,50,255),(0,0,255),"Leave Shop",(255,255,0),self.closeShopHandle,self)
        self.shopPanel = Panel(Vec2D(50,50), Vec2D(width-100,height-100), (0,60,255), [])
        self.itemPanel = Panel(Vec2D(5,100), Vec2D(width-110,height-205), (0,30,255), [])
        self.shopPanel.add(self.closeShopButton)
        self.shopPanel.add(self.itemPanel)
        self.buyable = []
        self.gui.add(self.shopPanel)
        self.gui.setActive(False)
        self.addBuyable(  500, "Efficient Engine", ImprovedEngineModifier(thePlayer), 4)
        self.addBuyable( 2000, "Laser Sight", LaserSightModifier(thePlayer), 2)
        self.addBuyable( 6000, "Automatic Gun", AutomaticGunModifier(thePlayer))
        self.addBuyable( 1000, "Bigger Bullets", LargerBulletModifier(thePlayer), 4)
        self.addBuyable( 2000, "Rapid Fire", RapidFireModifier(thePlayer), 3)
        self.addBuyable(20000, "Auto Evasion", AutoEvasionModifier(thePlayer))
    def addBuyable(self, price, name, mod, maxLevel = 1):
        if maxLevel < 1: maxLevel = 1
        if maxLevel > 1: name += " 1"
        button = Button(Vec2D(5, 10 + len(self.buyable) * 30),Vec2D(100,20),(50,50,255),(0,0,255),name,(255,255,0),self.buyItemButton, (self, len(self.buyable), None))
        self.buyable.append((price, name, mod, button, 0, maxLevel))
        self.itemPanel.add(button)
    def buyItemButton(button, (self, index, context)):
        price, name, mod, button, level, maxLevel = self.buyable[index]
        level = level + 1
        if level == 1:
            if not self.purchaseSomething(price, name, mod, context): return
            context.toastManager.popup("You bought '%s' for %s points!" % (name, price))
            if level < maxLevel:
                name = name[:-2] + " " + str(level + 1)
            button.text = name
            self.buyable[index] = (price, name, mod, button, level, maxLevel)
        else:
            if not self.upgradeSomething(price, name, mod, button, level, maxLevel, context): return
            context.toastManager.popup("You upgraded '%s' for %s points!" % (name, price))
            if level < maxLevel:
                name = name[:-2] + " " + str(level + 1)
            button.text = name
            self.buyable[index] = (price * 1.5, name, mod, button, level, maxLevel)
        if level == maxLevel:
            button.enabled = False
    def upgradeSomething(self, price, name, mod, button, level, maxLevel, context):
        confirmPurchase = PopupMessageYesNo("Upgrade %s (%s points)?" % (name, price), (50,50,255), (255,255,0))
        result = confirmPurchase.activate(None, context)
        if not result: return False
        if self.player.score < price + 100:
            alert = PopupMessageOK("You cannot afford this item!", (255,50,50), (255,255,0))
            alert.activate(None, context)
            return False
        self.player.modifiers.remove(mod)
        mod = mod.upgrade()
        self.player.addModifier(mod)
        self.player.score -= price
        return True
    def purchaseSomething(self, price, name, mod, context):
        confirmPurchase = PopupMessageYesNo("Purchase %s (%s points)?" % (name, price), (50,50,255), (255,255,0))
        result = confirmPurchase.activate(None, context)
        if not result: return False
        if self.player.score < price + 100:
            alert = PopupMessageOK("You cannot afford this item!", (255,50,50), (255,255,0))
            alert.activate(None, context)
            return False
        self.player.addModifier(mod)
        self.player.score -= price
        return True
    def closeShopHandle(button, self):
        self.gui.setActive(False)
    def render(self, dest):
        self.gui.render(dest)
    def think(self, others, context):
        for price, name, mod, button, level, maxLevel in self.buyable:
            button.arg = (button.arg[0], button.arg[1], context)
        if self.gui.active:
            exitShop = False
            limitFps = pygame.time.Clock()
            while not exitShop and self.gui.active:
                limitFps.tick(30)
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN and (event.key == pygame.K_b or event.key == pygame.K_ESCAPE):
                        self.gui.setActive(False)
                        exitShop = True
                    else:
                        self.gui.notify(event)
                context.screen.fill((0,0,0))
                self.gui.think(others, context)
                self.gui.render(context.screen)
                pygame.display.flip()
            self.player.paused = True
    def notify(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_b:
            if not self.gui.active:
                self.gui.setActive(True)

class Player(Entity):
    def __init__(self, pos):
        Entity.__init__(self, pos)
        self.gameConfig = INIFile("settings.ini")
        self.gameConfig.readonly = False # it will error if the file didn't exist, but we'll generate it if it broke
        if not self.gameConfig.hasSection("misc"):
            self.gameConfig.sections["misc"] = {}
        if not self.gameConfig.hasValue("misc","highestScore"):
            self.gameConfig.sections["misc"]["highestScore"] = 0.0
        if not self.gameConfig.hasValue("misc", "doneTutorial"):
            self.gameConfig.sections["misc"]["doneTutorial"] = "False"
        self.modifiers = []
        self.renderBounds = ((-20,-20),(20,20))
        self.lastShot = time.clock()
        self.shotDelay = 200 # ms
        self.lastNotified = time.clock()
        self.notifyDelay = 5000.0
        self.bearing = 0.0
        self.automatic = False
        self.friction = 0.999
        self.bulletSize = 4
        self.bulletSpeed = 6.0
        self.size = 10
        self.lostGame = False
        self.bestScoreEver = float(self.gameConfig.sections["misc"]["highestScore"])
        self.score = 100.0
        self.spreeStart = 0.0
        self.spreeTime = 1000.0 # kills must be <= a second apart
        self.scoreMultiplier = 1.0
        self.highestScore = self.score
        if self.highestScore > self.bestScoreEver:
            self.bestScoreEver = self.highestScore
            self.gameConfig.sections["misc"]["highestScore"] = self.bestScoreEver
        self.fuelCost = 1.0
        self.accelNow = [0.0,0.0]
        self.accel = 0.1
        self.fire = False
        self.paused = False
        self.rotVel = 0.05
        self.emitter = ParticleEmitter(self.pos, 400, [1,50], [2,6],\
                                       [200,2000], [[255,100,0],[255,255,0],\
                                                    [50,50,50],[100,100,100]])
        self.pewpewEmitter = ParticleEmitter(self.pos, 300, None, [1,2],\
                                             [200,1000], [(0,0,255), (50,50,255), (100,100,255)])
    def popup(self, context, text, override = False):
        if (time.clock() >= self.lastNotified + (self.notifyDelay / 1000.0)) or override:
            context.toastManager.popup(text)
            self.lastNotified = time.clock()
    def addModifier(self, mod):
        self.modifiers.append(mod)
        mod.initialiseMod()
    def accelerate(self, amplitude):
        mx, my = self.vel.get()
        mx += math.cos(self.bearing) * amplitude
        my += math.sin(self.bearing) * amplitude
        self.vel = Vec2D(mx, my)
    def render(self, dest):
        for mod in self.modifiers:
            mod.render(dest)
        secondPoint = [self.pos.getX(), self.pos.getY()]
        secondPoint[0] += math.cos(self.bearing) * 20
        secondPoint[1] += math.sin(self.bearing) * 20
        self.emitter.render(dest)
        self.pewpewEmitter.render(dest)
        pygame.draw.line(dest, (255,255,255), self.pos.getInt(), secondPoint)
        pygame.draw.circle(dest, (255,0,0), self.pos.getInt(), int(self.size))
    def tutorial(self, text, size, context):
        PopupMessageOK(text, (50,50,255),(255,255,0), size).activate(None, context)
    def think(self, others, context):
        if self.gameConfig.getValue("misc", "doneTutorial") != "True":
            self.gameConfig.makeValue("misc", "doneTutorial", "True")
            self.tutorial("Since this is (presumably) your first time playing the game, here are some tips!", 20, context)
            self.tutorial("Use W, A, S and D to fly, SPACE to pew pew and B to open the shop!", 20, context)
            self.tutorial("Hit asteroids for points, hit several in a row for multipliers!", 20, context)
            self.tutorial("That's it! Now shoot stuff!", 40, context)
            self.tutorial("Oh yeah, it goes without saying but, don't touch the asteroids :/", 20, context)
            self.gameConfig.save()
        if self.paused:
            pauseGame = PopupMessageOK("The game is paused, press OK to continue!", (50,50,255),(255,255,0))
            pauseGame.activate(None, context)
            self.paused = False
        if self.lostGame:
            context.reset = True
            keyPressed = False
            font = makeFont(40)
            gameOver = font.render("Game Over!", True, (255,255,255))
            pressAnyKey = font.render("Press any key to try again!", True, (255,255,255))
            ignoreDelay = 1000
            width, height = getResolution()
            ignoreStart = time.clock()
            limitFps = pygame.time.Clock()
            while not keyPressed:
                limitFps.tick(30)
                for event in pygame.event.get():
                    if time.clock() >= ignoreStart + (ignoreDelay / 1000.0):
                        if event.type == pygame.KEYDOWN:
                            keyPressed = True
                context.screen.fill((0,0,0))
                context.screen.blit(gameOver, ((width - gameOver.get_size()[0])/2, height / 2, 0,0))
                context.screen.blit(pressAnyKey, ((width - pressAnyKey.get_size()[0])/2, height / 2 + 36, 0,0))
                pygame.display.flip()
            return
        for mod in self.modifiers:
            mod.think(others, context)
        if self.score > self.highestScore:
            popupText = "Woot! New high score for this round!"
            self.highestScore = self.score
            if self.highestScore > self.bestScoreEver:
                bonusSize = 100
                popupText += " You beat the best score ever! Bonus %s points!" % bonusSize
                self.score += bonusSize
                self.highestScore += 100
                self.bestScoreEver = self.highestScore
                self.gameConfig.sections["misc"]["highestScore"] = self.bestScoreEver
                self.gameConfig.save()
            self.popup(context, popupText)
        if self.fire and time.clock() >= self.lastShot + (self.shotDelay / 1000.0):
            self.lastShot = time.clock()
            self.score -= 1
            if not self.automatic:
                self.fire = False
            x, y = self.pos.get()
            newBullet = Bullet(Vec2D(x,y), self.bulletSize, self.bearing, self.bulletSpeed, self)
            newBullet.setClipValues((0,0), getResolution(), True)
            newBullet.vel.x += self.vel.x
            newBullet.vel.y += self.vel.y
            others.append(newBullet)
            partCount = random.randint(2,4)
            self.accelerate(-self.accel*2.0)
            for x in range(partCount):
                myX, myY = self.pos.get()
                self.pewpewEmitter.pos = Vec2D(myX, myY)
                theAngle = random.randint(1,360)*math.pi/180
                thePower = random.randint(10,30)/10.0
                self.pewpewEmitter.setDirection(theAngle, thePower)
                self.pewpewEmitter.emit()
        self.accelerate(self.accelNow[0])
        self.score -= self.fuelCost * math.fabs(self.accelNow[0])
        self.bearing += self.accelNow[1]
        self.emitter.setDirection(self.bearing+math.pi, 5.0*self.accelNow[0])
        self.emitter.pos = self.pos
        self.emitter.think(None, context)
        self.pewpewEmitter.think(None, context)
        for entity in others:
            if entity is self: continue
            if not isinstance(entity, Asteroid): continue
            mx, my = self.pos.get()
            ax, ay = entity.pos.get()
            dx, dy = mx-ax, my-ay
            distance = math.sqrt((dx*dx)+(dy*dy))
            if distance <= self.size + entity.size:
                self.lostGame = True
        if self.score <= 0.0:
            self.lostGame = True
    def notify(self, event):
        for mod in self.modifiers:
            mod.notify(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                self.accelNow[0] = self.accel
            elif event.key == pygame.K_s:
                self.accelNow[0] = -self.accel
            elif event.key == pygame.K_a:
                self.accelNow[1] = -self.rotVel
            elif event.key == pygame.K_d:
                self.accelNow[1] = self.rotVel
            elif event.key == pygame.K_SPACE:
                self.fire = True
            elif event.key == pygame.K_p:
                self.paused = True
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_w or event.key == pygame.K_s:
                self.accelNow[0] = 0
            elif event.key == pygame.K_a:
                self.accelNow[1] = 0
            elif event.key == pygame.K_d:
                self.accelNow[1] = 0
            elif event.key == pygame.K_SPACE:
                self.fire = False

class GameContext:
    def __init__(self):
        self.run = True
        self.reset = False

def runGame():
    pygame.init()
    width, height = getResolution()
    flags = 0
    if isFullscreen():
        flags += pygame.FULLSCREEN
    screen = pygame.display.set_mode((width, height), flags)
    clock = pygame.time.Clock()
    pygame.font.init()
    myFont = makeFont(10)
    context = GameContext()
    context.screen = screen
    toastManager = ToastManager(10,(50,50,255),(255,255,0),3000,Vec2D(0,height+2),ToastManager.up,0.5)
    context.toastManager = toastManager
    while context.run:
        reset = False
        thePlayer = Player(Vec2D(float(width/2),float(height/2)))
        thePlayer.setClipValues((0,0),(width,height),True)
        spawner = EntitySpawner(Vec2D(0.0,0.0), AsteroidFactory(thePlayer), [500,5000], 10)
        upgradeShop = UpgradeShop(thePlayer)
        entities = [ thePlayer, spawner, upgradeShop, toastManager ]
        if thePlayer.gameConfig.hasValue("misc","doneTutorial") == False\
           or thePlayer.gameConfig.getValue("misc","doneTutorial") == "False":
            toastManager.popup("Welcome to Asteroids Survival! :)")
        while context.run and not context.reset:
            clock.tick(60)
            fps = clock.get_fps()
            fpsColour = (0,255,0)
            if fps <= 50: fpsColour = (255,255,0)
            if fps <= 40: fpsColour = (255,0,0)
            eventsToSend = []
            for event in pygame.event.get():
                if event.type == pygame.QUIT\
                   or event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    confirmExit = PopupMessageYesNo("Are you sure you want to quit?", (50,50,255), (255,255,0))
                    result = confirmExit.activate(None, context)
                    if result:
                        context.run = False
                        break
                else:
                    eventsToSend.append(event)
            toRemove = []
            for entity in entities:
                for event in eventsToSend:
                    entity.notify(event)
                entity.think(entities, context)
                if entity.removeMe and entity not in toRemove:
                    toRemove.append(entity)
                else:
                    entity.move()
            for bad in toRemove:
                entities.remove(bad)
            screen.fill((0,0,0))
            for entity in entities:
                if entity.onScreen((0,0), (width,height)):
                    entity.render(screen)
            fpsRender = myFont.render("FPS: %s" % fps, True, fpsColour)
            pygame.Surface.blit(screen, fpsRender, (0,0,0,0))
            entityCounter = myFont.render("Entities: %s" % len(entities), True, (255,255,255))
            pygame.Surface.blit(screen, entityCounter, (0,height - 10,0,0))
            scoreBoard = myFont.render("Score Remaining to Spend: %s" % thePlayer.score, True, (255,255,255))
            pygame.Surface.blit(screen, scoreBoard, ((width - scoreBoard.get_size()[0]) / 2, 5, 0,0))
            highestScore = myFont.render("Total Score This Round: %s" % thePlayer.highestScore, True, (255,255,0))
            pygame.Surface.blit(screen, highestScore, ((width - highestScore.get_size()[0]) / 2, 15, 0,0))
            bestScore = myFont.render("Best Score Ever: %s" % thePlayer.bestScoreEver, True, (255,100,100))
            pygame.Surface.blit(screen, bestScore, ((width - bestScore.get_size()[0]) / 2, 25, 0,0))
            pygame.display.flip()
        entities = []
        context.reset = False

if __name__ == "__main__":
    try:
        loadGraphicsSettings()
        runGame()
    except:
        sys.excepthook(*sys.exc_info())
        raw_input("press enter...")
