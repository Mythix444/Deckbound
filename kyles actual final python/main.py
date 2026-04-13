import pygame
import math
import time
import os
import random


assets = os.path.join(os.path.dirname(__file__), "assets")
cardImages = os.path.join(assets, "card")

def collision(sprite1, sprite2):
    rect1 = pygame.Rect(sprite1.position.x, sprite1.position.y, sprite1.hitbox.x, sprite1.hitbox.y)
    rect2 = pygame.Rect(sprite2.position.x, sprite2.position.y, sprite2.hitbox.x, sprite2.hitbox.y)
    return rect1.colliderect(rect2)

class sprite:
    def __init__(self, image, position, hitbox, collisions=None):
        self.image = image
        self.position = pygame.math.Vector2(position)
        self.hitbox = pygame.math.Vector2(hitbox)
        if not collisions is None:
            self.collisions = collisions
        else: 
            self.collisions = None
    def display(self, screen, positionOffset = pygame.math.Vector2(0, 0)):
        screen.blit(self.image, self.position + positionOffset)
    @property
    def x(self):
        return self.position.x
    @x.setter
    def x(self, value):
        self.position.x = value
    @property
    def y(self):
        return self.position.y
    @y.setter
    def y(self, value):
        self.position.y = value
    
    def move(self, vector):
        self.position.x += vector.x
        horizontalCollision = False
        if not self.collisions is None:
            for sprite in self.collisions:
                if collision(self, sprite):
                    horizontalCollision = True
                    if vector.x > 0:
                        self.position.x = sprite.position.x - self.hitbox[0] + 0
                    elif vector.x < 0:
                        self.position.x = sprite.position.x + sprite.hitbox[0]
        self.position.y += vector.y
        verticalCollision = False
        if not self.collisions is None:
            for sprite in self.collisions:
                if collision(self, sprite):
                    verticalCollision = True
                    if vector.y > 0:
                        self.position.y = sprite.position.y - self.hitbox[1] + 0.1
                    elif vector.y < 0:
                        self.position.y = sprite.position.y + sprite.hitbox[1]
        return horizontalCollision, verticalCollision


class screen:
    def __init__(self, *args):
        self.surface = pygame.display.set_mode(*args)
        self.camera = pygame.math.Vector2(0, 0)
    def __getattr__(self, name):
        return getattr(self.surface, name)
    def blit(self, image, position):
        self.surface.blit(image, position - (self.camera - (self.get_size()[0]/2, self.get_size()[1]/2)))
    def centerAround(self, centerPosition):
        if isinstance(centerPosition, sprite):
            self.camera = centerPosition.position + (centerPosition.hitbox[0]/2, centerPosition.hitbox[1]/2)
        elif isinstance(centerPosition, (pygame.math.Vector2, tuple)):
            self.camera = pygame.math.Vector2(centerPosition)
    def follow(self, targetPosition, strength, deltaTime):
        if isinstance(targetPosition, sprite):
            self.camera += (targetPosition.position - self.camera + (targetPosition.hitbox[0]/2, targetPosition.hitbox[1]/2)) * strength * deltaTime
            difference = self.camera - targetPosition.position - (targetPosition.hitbox[0]/2, targetPosition.hitbox[1]/2)
        elif isinstance(targetPosition, (pygame.math.Vector2, tuple)):
            self.camera += (pygame.math.Vector2(targetPosition) - self.camera) * strength * deltaTime
            difference = self.camera - pygame.math.Vector2(targetPosition)
            if abs(difference.x) < 0.5:
                self.camera.x = pygame.math.Vector2(targetPosition).x
            if abs(difference.y) < 0.5:
                self.camera.y = pygame.math.Vector2(targetPosition).y
        self.camera = pygame.math.Vector2(round(self.camera.x), round(self.camera.y))


window = screen((800, 600), pygame.RESIZABLE | pygame.SCALED)
playerImage = pygame.image.load(os.path.join(assets, "player.png"))
playerImage = pygame.transform.scale(playerImage, (75, 75))

brickImage = pygame.image.load(os.path.join(assets, "stonebrick.png")).convert_alpha()
brickImage = pygame.transform.smoothscale(brickImage, (75, 75))

daggerImage = pygame.image.load(os.path.join(assets, "dagger.png")).convert_alpha()
daggerImage = pygame.transform.smoothscale(daggerImage, (75, 75))

tilemap = []

running = True
player = sprite(playerImage, (0, 0), (75, 75), tilemap)
clock = pygame.time.Clock()
delta = time.time()

tilemap.append(sprite(brickImage, (0, 100), (75, 75)))
tilemap.append(sprite(brickImage, (75, 100), (75, 75)))
tilemap.append(sprite(brickImage, (0, 175), (75, 75)))
tilemap.append(sprite(brickImage, (75, 175), (75, 75)))
tilemap.append(sprite(brickImage, (150, 100), (75, 75)))
tilemap.append(sprite(brickImage, (150, 175),(75, 75)))

class Tween:
    easingStyles = {
        "Linear": "linear",
        "Quad": "quad",
        "Cubic": "cubic",
        "Quart": "quart",
        "Quint": "quint",
        "Sine": "sine",
        "Exponential": "exponential",
        "Circular": "circular",
        "Elastic": "elastic",
        "Back": "back",
        "Bounce": "bounce"
    }
    
    def __init__(self, duration, startValue, endValue, introTween=None, outroTween=None):
        self.duration = duration
        self.startValue = startValue
        self.currentValue = startValue
        self.endValue = endValue
        self.introTween = introTween
        self.outroTween = outroTween
        
        self.elapsedTime = 0
        self.isPlaying = False
        self.isCompleted = False
        
        self.onComplete = None
    
    def play(self):
        self.isPlaying = True
        self.isCompleted = False
        self.elapsedTime = 0
    
    def pause(self):
        self.isPlaying = False
    
    def resume(self):
        self.isPlaying = True
    
    def cancel(self):
        self.isPlaying = False
        self.isCompleted = True
    
    def update(self, deltaTime):
        if not self.isPlaying or self.isCompleted:
            return self.getValue(1.0 if self.isCompleted else 0.0)
        
        self.elapsedTime += deltaTime
        
        if self.elapsedTime >= self.duration:
            self.isPlaying = False
            self.isCompleted = True
            if self.onComplete:
                self.onComplete()
            return self.getValue(1.0)
        
        progress = self.elapsedTime / self.duration
        easedProgress = self.applyEasing(progress)
        

        value = self.getValue(easedProgress)
        self.currentValue = value
        return value
    
    def getValue(self, progress):
        if isinstance(self.startValue, dict):
            result = {}
            for key in self.startValue:
                start = self.startValue[key]
                end = self.endValue[key]
                result[key] = start + (end - start) * progress
            return result
        else:
            return self.startValue + (self.endValue - self.startValue) * progress
    
    def getDerivative(self, style, t, epsilon=0.0001):
        f1 = self.evaluateEasing(style, t - epsilon)
        f2 = self.evaluateEasing(style, t + epsilon)
        return (f2 - f1) / (2 * epsilon)
    
    def evaluateEasing(self, style, t):
        t = max(0.0, min(1.0, t))
        if style == "Linear":
            return t
        elif style == "Quad":
            return self.quadIn(t)
        elif style == "Cubic":
            return self.cubicIn(t)
        elif style == "Quart":
            return self.quartIn(t)
        elif style == "Quint":
            return self.quintIn(t)
        elif style == "Sine":
            return self.sineIn(t)
        elif style == "Exponential":
            return self.exponentialIn(t)
        elif style == "Circular":
            return self.circularIn(t)
        elif style == "Elastic":
            return self.elasticIn(t)
        elif style == "Back":
            return self.backIn(t)
        elif style == "Bounce":
            return self.bounceOut(t)
        return t
    
    def applyEasing(self, progress):
        if self.introTween is None and self.outroTween is None:
            return progress
        elif self.introTween is None:
            if self.outroTween == "Bounce":
                return self.bounceOut(progress)
            elif self.outroTween == "Elastic":
                return self.elasticOut(progress)
            elif self.outroTween == "Back":
                return self.backOut(progress)
            else:
                return 1.0 - self.getEasingFunction(self.outroTween)(1.0 - progress)
        elif self.outroTween is None:
            if self.introTween == "Bounce":
                return self.bounceIn(progress)
            elif self.introTween == "Elastic":
                return self.elasticIn(progress)
            elif self.introTween == "Back":
                return self.backIn(progress)
            else:
                return self.getEasingFunction(self.introTween)(progress)
        else:
            if progress < 0.5:
                t = progress * 2.0
                if self.introTween == "Bounce":
                    return self.bounceIn(t) * 0.5
                elif self.introTween == "Elastic":
                    return self.elasticIn(t) * 0.5
                elif self.introTween == "Back":
                    return self.backIn(t) * 0.5
                else:
                    return self.getEasingFunction(self.introTween)(t) * 0.5
            else:
                t = (progress - 0.5) * 2.0
                if self.introTween == "Bounce":
                    introValue = self.bounceIn(1.0) * 0.5
                elif self.introTween == "Elastic":
                    introValue = self.elasticIn(1.0) * 0.5
                elif self.introTween == "Back":
                    introValue = self.backIn(1.0) * 0.5
                else:
                    introValue = self.getEasingFunction(self.introTween)(1.0) * 0.5
                
                if self.outroTween == "Bounce":
                    outroEased = self.bounceOut(t)
                elif self.outroTween == "Elastic":
                    outroEased = self.elasticOut(t)
                elif self.outroTween == "Back":
                    outroEased = self.backOut(t)
                else:
                    outroEased = 1.0 - self.getEasingFunction(self.outroTween)(1.0 - t)
                    
                    if self.introTween not in ["Bounce", "Elastic", "Back"] and self.outroTween not in ["Bounce", "Elastic", "Back"]:
                        introVelocity = self.getDerivative(self.introTween, 1.0) * 2.0
                        outroVelocity = self.getDerivative(self.outroTween, 1.0) * 2.0
                        
                        if outroVelocity != 0:
                            velocityRatio = introVelocity / outroVelocity
                            outroEased = outroEased * velocityRatio
                            outroEased = max(0.0, min(1.0, outroEased))
                
                return introValue + (1.0 - introValue) * outroEased
    
    def getEasingFunction(self, style):
        if style == "Linear":
            return lambda t: t
        elif style == "Quad":
            return self.quadIn
        elif style == "Cubic":
            return self.cubicIn
        elif style == "Quart":
            return self.quartIn
        elif style == "Quint":
            return self.quintIn
        elif style == "Sine":
            return self.sineIn
        elif style == "Exponential":
            return self.exponentialIn
        elif style == "Circular":
            return self.circularIn
        elif style == "Elastic":
            return self.elasticIn
        elif style == "Back":
            return self.backIn
        elif style == "Bounce":
            return self.bounceOut
        return lambda t: t
    
    def quadIn(self, t):
        return t * t
    
    def cubicIn(self, t):
        return t * t * t
    
    def quartIn(self, t):
        return t * t * t * t
    
    def quintIn(self, t):
        return t * t * t * t * t
    
    def sineIn(self, t):
        return 1.0 - math.cos((t * math.pi) / 2.0)
    
    def exponentialIn(self, t):
        return 0.0 if t == 0.0 else math.pow(2.0, 10.0 * t - 10.0)
    
    def circularIn(self, t):
        return 1.0 - math.sqrt(1.0 - t * t)
    
    def elasticIn(self, t):
        if t == 0.0:
            return 0.0
        elif t == 1.0:
            return 1.0
        else:
            c4 = (2.0 * math.pi) / 3.0
            return -(math.pow(2.0, 10.0 * t - 10.0) * math.sin((t * 10.0 - 10.75) * c4))
    
    def elasticOut(self, t):
        if t == 0.0:
            return 0.0
        elif t == 1.0:
            return 1.0
        else:
            c4 = (2.0 * math.pi) / 3.0
            return math.pow(2.0, -10.0 * t) * math.sin((t * 10.0 - 0.75) * c4) + 1.0
    
    def backIn(self, t):
        c1 = 1.70158
        c3 = c1 + 1.0
        return c3 * t * t * t - c1 * t * t
    
    def backOut(self, t):
        c1 = 1.70158
        c3 = c1 + 1.0
        return 1.0 + c3 * (t - 1.0) * (t - 1.0) * (t - 1.0) + c1 * (t - 1.0) * (t - 1.0)
    
    def bounceIn(self, t):
        return 1.0 - self.bounceOut(1.0 - t)
    
    def bounceOut(self, t):
        n1 = 7.5625
        d1 = 2.75
        
        if t < 1.0 / d1:
            return n1 * t * t
        elif t < 2.0 / d1:
            t -= 1.5 / d1
            return n1 * t * t + 0.75
        elif t < 2.5 / d1:
            t -= 2.25 / d1
            return n1 * t * t + 0.9375
        else:
            t -= 2.625 / d1
            return n1 * t * t + 0.984375
daggers = []

for i in range(5):
    daggers.append(sprite(daggerImage, (0, 0), (75, 75)))

#daggers.append(sprite(daggerImage, (0, 0), (75, 75)))



tarnishedBack = pygame.image.load(os.path.join(cardImages, "Tarnished.png")).convert_alpha()
tarnishedBack = pygame.transform.smoothscale(tarnishedBack, (150, 225))
tempBack = pygame.image.load(os.path.join(cardImages, "tempBack.png")).convert_alpha()

class Deck():
    def __init__(self):
        self.cards = []
        self.drawnCards = []
        self.cooldown = 0
        self.maxCooldown = 0.05
        self.drawnCardAmount = 0
    def shuffle(self):
        random.shuffle(self.cards)
    def draw(self, amount=1):
        self.drawnCardAmount = amount
        return self._draw()
    def _draw(self):
        if not self.cards == []:
            card = self.cards.pop(random.randint(0, len(self.cards)-1))
            self.drawnCards.append(card)
            card.tweens["position"] = Tween(0.25, 0, 300, None, "Back")
            card.tweens["position"].play()
    def discard(self, card):
        self.drawnCards.remove(card)
        self.cards.append(card)
    def addCard(self, card=None, amount=1):
        for i in range(amount):
            self.cards.append(card if not card == None else Card())
    def update(self, deltaTime):
        self.cooldown -= deltaTime
        if self.cooldown <= 0:
            if self.drawnCardAmount > 0:
                self.drawnCardAmount -= 1
                self.cooldown = self.maxCooldown
                self._draw()
        for card in self.drawnCards:
            card.update(deltaTime)

class Tweens():
    def __init__(self):
        self.tweens = {}
    def addTween(self, tween):
        self.tweens.append(tween)
    def update(self, deltaTime):
        for tween in self.tweens:
            value = tween.update(deltaTime)
            



class Card(sprite):
    def __init__(self):
        randomNum = random.randint(1, 1)
        if randomNum == 1:
            self.image = tarnishedBack
        super().__init__(tarnishedBack, (0, 0), (150, 210))
        self.xOffset = 0
        self.flipped = False
        self.done = False
        self.tweens = {}
    def update(self, deltaTime):
        removeTweens = []
        for tween in self.tweens:
            value = self.tweens[tween].update(deltaTime)
            if self.tweens[tween] is not None:
                if tween == "position":
                    self.position.y = 300 - value
                if tween == "seperate":
                    self.position.x = value
                if tween == "flip":
                    if self.flipped:
                        self.image = pygame.transform.scale(tempBack, (value, 225))
                    else:
                        self.image = pygame.transform.scale(tarnishedBack, (value, 225))
            if self.tweens[tween].isCompleted:
                if not tween == "flip" or self.flipped:
                    removeTweens.append(tween)
        
        for tween in self.tweens:
            if tween == "flip":
                if self.tweens[tween].isCompleted and self.image.get_width() < 10 and self.flipped:
                    deck.drawnCards.remove(self)
            if tween == "flip" and self.image.get_width() < 10 and not self.flipped:
                self.flipped = True
                self.tweens["flip"] = Tween(0.25, 0, 150, None, "Circular")
                self.tweens["flip"].play()
        for tween in removeTweens:
            self.tweens.pop(tween, None)

daggerRotation = 0

def daggerOrbit(sprite, center, radius, angle):
    target_x = center.x + math.cos(math.radians(angle)) * radius
    target_y = center.y + math.sin(math.radians(angle)) * radius

    image = daggerImage
    sprite.image = pygame.transform.rotozoom(image, -angle - 90, 1)

    sprite.x = target_x - sprite.image.get_width() / 2 + 37
    sprite.y = target_y - sprite.image.get_height() / 2 + 37


deck = Deck()

cardDebounce = False

cardsLeft = 0
cardCooldown = 0
closeCards = False

def mouseIntersect(sprite, mousePos):
    try:
        xOffset = sprite.xOffset
    except:
        xOffset = 0
    rect = pygame.Rect(sprite.position.x + xOffset, sprite.position.y, sprite.hitbox.x, sprite.hitbox.y)
    if isinstance(sprite, Card):
        rect.x -= sprite.hitbox.x/2
        rect.y -= sprite.hitbox.y/2
        
        rect.x += window.camera.x
        rect.y += window.camera.y
        
    rectImage = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    rectImage.fill((0, 0, 255)) 
    return rect.collidepoint(mousePos.x, mousePos.y)



mouseClick = False
mouseDown = False

test = {}

while running:
    clock.tick(60)
    mouseClick = False
    keys = pygame.key.get_pressed()
    window.fill((255, 255, 255))
    delta = time.time() - delta
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mousePosition = pygame.math.Vector2(pygame.mouse.get_pos()) + (window.camera - (window.get_size()[0]/2, window.get_size()[1]/2))
            if not mouseDown:
                mouseClick = True
    
    mousePosition = pygame.math.Vector2(pygame.mouse.get_pos()) + (window.camera - (window.get_size()[0]/2, window.get_size()[1]/2))
    mouseDown = pygame.mouse.get_pressed()[0]
            
    if keys[pygame.K_a] or keys[pygame.K_d] or keys[pygame.K_w] or keys[pygame.K_s]:
        player.move((pygame.math.Vector2(keys[pygame.K_d] - keys[pygame.K_a], keys[pygame.K_s] - keys[pygame.K_w])).normalize() * 300 * delta)

    if keys[pygame.K_r]:
        if not cardDebounce:
            cardDebounce = True
            deck.addCard(amount=5)
            deck.draw(amount=5)
    else:
        cardDebounce = False
            
    
    if not deck.drawnCards == []:
        try:
            if all(all((tween.isCompleted or card.tweens[tween] == "flip") for tween in card.tweens.values()) for card in deck.drawnCards):
                cardLength = len(deck.drawnCards)
                cardNumber = 1
                for card in deck.drawnCards:
                    card.tweens.pop("position", None)
                    createTween = False
                    try:
                        if card.tweens["seperate"].isPlaying:
                            createTween = True
                    except:
                        createTween = True
                    if createTween:
                        card.tweens["seperate"] = Tween(0.35, card.position.x, ((cardNumber - 1) * 150) - ((cardLength - 1) * 150 / 2), "Circular", "Back")
                        card.tweens["seperate"].play()
                    cardNumber += 1
        except:
            pass
    for card in deck.drawnCards:
        if mouseIntersect(card, mousePosition):
            if mouseClick:
                positionTweens = []
                for carD in deck.drawnCards:
                    for tween in carD.tweens:
                        if tween == "position" or tween == "seperate":
                            positionTweens.append(carD.tweens[tween])
                def flipTween():
                    card.tweens["flip"] = Tween(0.25, 150, 0, "Circular", None)
                    card.tweens["flip"].play()
                    card.done = True
                if all(tween.currentValue == tween.endValue for tween in positionTweens):
                    try:
                        try:
                            if not card.tweens["flip"].isPlaying:
                                flipTween()
                        except:
                            flipTween()
                    except:
                        pass
    window.follow(player, 15, delta)

    for tile in tilemap:
        tile.display(window)

    player.display(window)

    for i, dagger in enumerate(daggers):
        daggerOrbit(dagger, player.position, 100, daggerRotation + i * 360 / len(daggers))
    deck.update(delta)
    for card in deck.drawnCards:
        card.display(window, pygame.math.Vector2((150 - card.image.get_width()) / 2, 0) + window.camera - (card.hitbox / 2))

    pygame.display.flip()

    delta = time.time()