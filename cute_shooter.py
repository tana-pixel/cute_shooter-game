import pygame
import random
import math
import json
import os

# --- ตั้งค่าเริ่มต้น ---
WIDTH, HEIGHT = 900, 600
FPS = 60

# โทนสีพาสเทล
PASTEL_BG = (250, 245, 255)
PASTEL_1 = (255, 182, 193)  # light pink
PASTEL_2 = (173, 216, 230)  # light blue
PASTEL_3 = (152, 251, 152)  # light green
PASTEL_4 = (255, 228, 181)  # moccasin
PASTEL_5 = (221, 160, 221)  # plum
INK = (60, 60, 60)
WHITE = (255, 255, 255)

SAVE_FILE = "cute_shooter_save.json"

# --- เตรียม mixer ก่อน init เพื่อลดดีเลย์ ---
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
try:
    pygame.mixer.init()
except Exception as e:
    print("pygame.mixer.init() failed:", e)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cute Shooter – เกมยิงปืนน่ารักๆ")
clock = pygame.time.Clock()

# --- ฟังก์ชันช่วยเหลือ ---
def load_save():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"highscore": 0}
    return {"highscore": 0}


def save_data(data):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def draw_text(surf, text, size, x, y, color=INK, center=True, bold=False):
    font = pygame.font.SysFont("THSarabunNew", size, bold=bold)
    img = font.render(text, True, color)
    rect = img.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surf.blit(img, rect)
    return rect


def clamp(v, a, b):
    return max(a, min(b, v))


# --- พาร์ติเคิลวิ๊ง ๆ ---
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = random.uniform(-2.0, -0.5)
        self.life = random.randint(20, 40)
        self.size = random.randint(2, 4)
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.05
        self.life -= 1

    def draw(self, surf):
        if self.life > 0:
            pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.size)


# --- กระสุน ---
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle_deg, speed=9):
        super().__init__()
        self.x = x
        self.y = y
        ang = math.radians(angle_deg)
        self.vx = math.cos(ang) * speed
        self.vy = math.sin(ang) * speed
        self.radius = 6
        self.color = PASTEL_2
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.rect.center = (self.x, self.y)
        # ออกนอกจอให้ฆ่า
        if self.x < -10 or self.x > WIDTH+10 or self.y < -10 or self.y > HEIGHT+10:
            self.kill()

    def draw(self, surf):
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.radius)


# --- ผู้เล่น (ตัวละครแมวน่ารัก) ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.x = WIDTH//2
        self.y = HEIGHT - 80
        self.speed = 5
        self.radius = 20
        self.color = PASTEL_5
        self.rect = pygame.Rect(self.x-20, self.y-20, 40, 40)
        self.shoot_cd = 0
        self.hp = 3
        self.invuln = 0
        self.power_triple = 0  # วินาทีของบัพยิงสามทาง

    def update(self, keys):
        dx = dy = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1

        # ปรับความเร็วแนวทแยงให้พอดี
        if dx and dy:
            dx *= 0.7071
            dy *= 0.7071

        self.x += dx * self.speed
        self.y += dy * self.speed
        self.x = clamp(self.x, 30, WIDTH-30)
        self.y = clamp(self.y, 30, HEIGHT-30)
        self.rect.center = (self.x, self.y)

        if self.shoot_cd > 0:
            self.shoot_cd -= 1
        if self.invuln > 0:
            self.invuln -= 1
        if self.power_triple > 0:
            self.power_triple -= 1

    def shoot(self, target_pos, bullets, sfx=None):
        if self.shoot_cd > 0:
            return
        # คำนวณมุมจากผู้เล่นไปเมาส์
        tx, ty = target_pos
        ang = math.degrees(math.atan2(ty - self.y, tx - self.x))
        if self.power_triple > 0:
            for off in (-12, 0, 12):
                bullets.add(Bullet(self.x, self.y, ang + off))
        else:
            bullets.add(Bullet(self.x, self.y, ang))
        self.shoot_cd = 10  # คูลดาวน์เล็กน้อย
        if sfx:
            try:
                sfx.play()
            except Exception:
                pass

    def hit(self):
        if self.invuln <= 0:
            self.hp -= 1
            self.invuln = 60  # 1 วินาทีอมตะหลังโดน
            return True
        return False

    def draw(self, surf):
        # ตัวแมววงรี + หูสามเหลี่ยม
        body_rect = pygame.Rect(0, 0, 48, 40)
        body_rect.center = (self.x, self.y)
        pygame.draw.ellipse(surf, self.color, body_rect)
        # หู
        pygame.draw.polygon(surf, self.color, [(self.x-12, self.y-12), (self.x-2, self.y-30), (self.x-20, self.y-24)])
        pygame.draw.polygon(surf, self.color, [(self.x+12, self.y-12), (self.x+2, self.y-30), (self.x+20, self.y-24)])
        # ตา
        eye_col = INK if (self.invuln//5)%2==0 else (200,200,200)
        pygame.draw.circle(surf, eye_col, (int(self.x-8), int(self.y-3)), 4)
        pygame.draw.circle(surf, eye_col, (int(self.x+8), int(self.y-3)), 4)
        # หนวด
        pygame.draw.line(surf, eye_col, (self.x-16, self.y+4), (self.x-30, self.y+2), 2)
        pygame.draw.line(surf, eye_col, (self.x-16, self.y+8), (self.x-30, self.y+10), 2)
        pygame.draw.line(surf, eye_col, (self.x+16, self.y+4), (self.x+30, self.y+2), 2)
        pygame.draw.line(surf, eye_col, (self.x+16, self.y+8), (self.x+30, self.y+10), 2)


# --- ศัตรู (เจลลี่น่ารัก) ---
class Enemy(pygame.sprite.Sprite):
    def __init__(self, level):
        super().__init__()
        self.radius = random.randint(14, 24)
        self.x = random.randint(self.radius, WIDTH - self.radius)
        self.y = -self.radius - 10
        base_speed = 1.6 + min(level*0.08, 3.0)
        self.vy = random.uniform(base_speed, base_speed + 1.2)
        self.vx = random.uniform(-0.8, 0.8)
        self.color = random.choice([PASTEL_1, PASTEL_2, PASTEL_3, PASTEL_4, PASTEL_5])
        self.hp = 1 if self.radius < 20 else 2
        self.rect = pygame.Rect(self.x-self.radius, self.y-self.radius, self.radius*2, self.radius*2)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if self.x < self.radius or self.x > WIDTH - self.radius:
            self.vx *= -1
        self.rect.center = (self.x, self.y)
        if self.y - self.radius > HEIGHT + 40:
            self.kill()

    def draw(self, surf):
        # เจลลี่เงา
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surf, WHITE, (int(self.x - self.radius//3), int(self.y - self.radius//4)), max(2, self.radius//5))


# --- ไอเทมบัพ ---
class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, kind):
        super().__init__()
        self.x = x
        self.y = y
        self.kind = kind  # 'heart' หรือ 'triple'
        self.vy = 2.2
        self.rect = pygame.Rect(self.x-12, self.y-12, 24, 24)

    def update(self):
        self.y += self.vy
        self.rect.center = (self.x, self.y)
        if self.y > HEIGHT + 30:
            self.kill()

    def draw(self, surf):
        if self.kind == 'heart':
            # วาดหัวใจง่าย ๆ
            x, y = int(self.x), int(self.y)
            pygame.draw.circle(surf, (255, 105, 180), (x-6, y-4), 6)
            pygame.draw.circle(surf, (255, 105, 180), (x+6, y-4), 6)
            pygame.draw.polygon(surf, (255, 105, 180), [(x-12, y-2), (x+12, y-2), (x, y+12)])
        else:
            pygame.draw.rect(surf, (255, 215, 0), pygame.Rect(self.x-10, self.y-10, 20, 20), border_radius=6)
            pygame.draw.circle(surf, WHITE, (int(self.x), int(self.y)), 3)


# --- ดาวพื้นหลัง ---
class Star:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.speed = random.uniform(0.2, 1.0)
        self.size = random.randint(1, 3)

    def update(self):
        self.y += self.speed
        if self.y > HEIGHT:
            self.y = 0
            self.x = random.randint(0, WIDTH)

    def draw(self, surf):
        pygame.draw.circle(surf, (240, 240, 255), (int(self.x), int(self.y)), self.size)


# --- เกม ---
class Game:
    def __init__(self):
        # โหลดข้อมูลง่าย ๆ แล้ว reset สถานะ
        self.data = load_save()
        self.highscore = self.data.get("highscore", 0)

        # เตรียมตัวแปรเสียง (ถ้าไม่มีไฟล์จะเป็น None)
        self.sfx_shoot = None
        self.sfx_pickup = None
        self.sfx_explosion = None
        self.music_loaded = False

        # โหลดเสียง (try/except ไม่ให้ crash)
        try:
            self.sfx_shoot = pygame.mixer.Sound("shoot.wav")
            self.sfx_shoot.set_volume(0.45)
            print("โหลด shoot.wav สำเร็จ")
        except Exception as e:
            print("ไม่พบ shoot.wav:", e)
            self.sfx_shoot = None

        try:
            self.sfx_pickup = pygame.mixer.Sound("pickup.wav")
            self.sfx_pickup.set_volume(0.6)
            print("โหลด pickup.wav สำเร็จ")
        except Exception as e:
            print("ไม่พบ pickup.wav:", e)
            self.sfx_pickup = None

        try:
            self.sfx_explosion = pygame.mixer.Sound("explosion.mp3")
            self.sfx_explosion.set_volume(0.5)
            print("โหลด explosion.wav สำเร็จ")
        except Exception as e:
            print("ไม่พบ explosion.wav:", e)
            self.sfx_explosion = None

        try:
            pygame.mixer.music.load("background.mp3")
            pygame.mixer.music.set_volume(0.28)
            self.music_loaded = True
            print("โหลด background.mp3 สำเร็จ (ยังไม่เล่นจนกว่าจะเริ่มเกม)")
        except Exception as e:
            print("ไม่พบ background.mp3:", e)
            self.music_loaded = False

        # สร้างข้อมูลเกมเริ่มต้น
        self.reset()

    def reset(self):
        # หยุดเพลงเมื่อกลับเมนู/รีเซ็ต
        try:
            if self.music_loaded:
                pygame.mixer.music.stop()
        except Exception:
            pass

        self.state = "menu"  # menu, playing, pause, gameover
        self.player = Player()
        self.bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.particles = []
        self.stars = [Star() for _ in range(90)]
        self.score = 0
        self.level = 1
        self.spawn_timer = 0
        self.spawn_cd = 45
        self.time_played = 0

    def spawn_enemy(self):
        self.enemies.add(Enemy(self.level))

    def drop_powerup(self, x, y):
        if random.random() < 0.15:
            kind = random.choice(['heart', 'triple', 'triple', 'heart'])
            self.powerups.add(PowerUp(x, y, kind))

    def update_menu(self):
        pass

    def update_playing(self):
        keys = pygame.key.get_pressed()
        self.player.update(keys)

        # ยิงด้วยคลิกเมาส์ซ้ายหรือ Space
        mouse_pressed = pygame.mouse.get_pressed()[0]
        if mouse_pressed:
            self.player.shoot(pygame.mouse.get_pos(), self.bullets, self.sfx_shoot)
        if keys[pygame.K_SPACE]:
            # ยิงตรงขึ้นถ้าไม่ใช้เมาส์
            self.player.shoot((self.player.x, self.player.y-1000), self.bullets, self.sfx_shoot)

        self.bullets.update()
        for e in list(self.enemies):
            e.update()
        for p in list(self.powerups):
            p.update()
        for s in self.stars:
            s.update()

        # สุ่มเกิดศัตรูเพิ่มตามเลเวล
        self.spawn_timer -= 1
        if self.spawn_timer <= 0:
            self.spawn_enemy()
            self.spawn_cd = max(12, 45 - int(self.level*1.7))
            self.spawn_timer = self.spawn_cd

        # ชนกระสุนกับศัตรู
        for e in list(self.enemies):
            for b in list(self.bullets):
                # ใช้ระยะวงกลมตรวจ
                if (e.rect.centerx - b.x)**2 + (e.rect.centery - b.y)**2 <= (e.radius + b.radius)**2:
                    b.kill()
                    e.hp -= 1
                    # พาร์ติเคิลระเบิดคิวท์ ๆ
                    for _ in range(10):
                        self.particles.append(Particle(e.x, e.y, e.color))
                    if e.hp <= 0:
                        # เล่นเสียงระเบิด
                        if self.sfx_explosion:
                            try:
                                self.sfx_explosion.play()
                            except Exception:
                                pass
                        self.score += 10
                        self.drop_powerup(e.x, e.y)
                        e.kill()
                        if self.score % 100 == 0:
                            self.level += 1

        # เก็บไอเทม
        if self.player and self.player.hp > 0:
            for pu in list(self.powerups):
                if self.player.rect.colliderect(pu.rect):
                    if pu.kind == 'heart':
                        self.player.hp = min(5, self.player.hp + 1)
                    else:
                        self.player.power_triple = 60 * 8  # 8 วินาที

                    # เล่นเสียงเก็บรางวัล
                    if self.sfx_pickup:
                        try:
                            self.sfx_pickup.play()
                        except Exception:
                            pass

                    for _ in range(15):
                        self.particles.append(Particle(pu.x, pu.y, (255, 215, 0)))
                    pu.kill()

        # ศัตรูชนผู้เล่น
        for e in list(self.enemies):
            dist2 = (e.x - self.player.x)**2 + (e.y - self.player.y)**2
            if dist2 <= (e.radius + self.player.radius)**2:
                if self.player.hit():
                    for _ in range(20):
                        self.particles.append(Particle(self.player.x, self.player.y, PASTEL_1))

        # อัพเดตพาร์ติเคิล
        for pt in list(self.particles):
            pt.update()
            if pt.life <= 0:
                self.particles.remove(pt)

        # เช็คจบเกม
        if self.player.hp <= 0:
            self.state = "gameover"
            self.highscore = max(self.highscore, self.score)
            save_data({"highscore": self.highscore})
            # หยุดเพลงเมื่อเกมจบ
            try:
                if self.music_loaded:
                    pygame.mixer.music.stop()
            except Exception:
                pass

        self.time_played += 1

    def draw_hud(self, surf):
        # แถบหัวใจ
        for i in range(self.player.hp):
            x = 20 + i*26
            y = 20
            pygame.draw.circle(surf, (255,105,180), (x-6, y), 7)
            pygame.draw.circle(surf, (255,105,180), (x+6, y), 7)
            pygame.draw.polygon(surf, (255,105,180), [(x-12, y+2), (x+12, y+2), (x, y+16)])
        # คะแนน & เลเวล
        draw_text(surf, f"คะแนน: {self.score}", 26, WIDTH-130, 24, center=False)
        draw_text(surf, f"เลเวล: {self.level}", 22, WIDTH-130, 52, center=False)
        # บัฟสามทาง
        if self.player.power_triple > 0:
            sec = self.player.power_triple // 60
            draw_text(surf, f"Triple: {sec}s", 22, WIDTH-130, 80, center=False, color=(120,120,120))

    def draw_bg(self, surf):
        surf.fill(PASTEL_BG)
        # กรอบโค้งมน
        pygame.draw.rect(surf, (255, 255, 255), pygame.Rect(10, 10, WIDTH-20, HEIGHT-20), border_radius=24)
        for s in self.stars:
            s.draw(surf)

    def draw_menu(self, surf):
        self.draw_bg(surf)
        draw_text(surf, "Cute Shooter", 64, WIDTH//2, 150, bold=True)
        draw_text(surf, "เกมยิงปืนน่ารักๆ ด้วย Python (Pygame)", 26, WIDTH//2, 210)
        draw_text(surf, "คลิกซ้ายหรือกด SPACE เพื่อยิง | เดิน: W A S D", 22, WIDTH//2, 250, color=(100,100,100))
        draw_text(surf, f"สถิติ: High Score {self.highscore}", 24, WIDTH//2, 290)
        draw_text(surf, "กด [ENTER] เพื่อเริ่ม", 28, WIDTH//2, 360, color=PASTEL_5, bold=True)
        draw_text(surf, "กด [M] เพื่อปิด/เปิดเมาส์เล็ง (เริ่มต้น: ใช้เมาส์เล็ง)", 18, WIDTH//2, 400, color=(120,120,120))

    def draw_pause(self, surf):
        draw_text(surf, "พักเกม", 48, WIDTH//2, HEIGHT//2 - 20)
        draw_text(surf, "กด [P] ต่อ | [ESC] ออกเมนู", 24, WIDTH//2, HEIGHT//2 + 30)

    def draw_gameover(self, surf):
        self.draw_bg(surf)
        draw_text(surf, "เกมจบแล้ว!", 56, WIDTH//2, 180, bold=True, color=PASTEL_1)
        draw_text(surf, f"คะแนน: {self.score}", 30, WIDTH//2, 240)
        draw_text(surf, f"สถิติสูงสุด: {self.highscore}", 26, WIDTH//2, 282)
        draw_text(surf, "[ENTER] เล่นอีกครั้ง  |  [ESC] กลับเมนู", 22, WIDTH//2, 330)

    def draw_playing(self, surf):
        self.draw_bg(surf)
        # วาดสไปรท์
        for e in self.enemies:
            e.draw(surf)
        for b in self.bullets:
            b.draw(surf)
        for p in self.powerups:
            p.draw(surf)
        self.player.draw(surf)
        # วาดพาร์ติเคิลทีหลังสุด
        for pt in self.particles:
            pt.draw(surf)
        self.draw_hud(surf)

    def run(self):
        running = True
        aim_with_mouse = True  # เริ่มต้นเล็งด้วยเมาส์

        while running:
            dt = clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if self.state == "menu":
                        if event.key == pygame.K_RETURN:
                            self.state = "playing"
                            # เริ่มเล่น background music ถ้ามี
                            try:
                                if self.music_loaded and not pygame.mixer.music.get_busy():
                                    pygame.mixer.music.play(-1)
                            except Exception:
                                pass
                    elif self.state == "playing":
                        if event.key == pygame.K_p:
                            self.state = "pause"
                    elif self.state == "pause":
                        if event.key == pygame.K_p:
                            self.state = "playing"
                        elif event.key == pygame.K_ESCAPE:
                            self.reset()
                    elif self.state == "gameover":
                        if event.key == pygame.K_RETURN:
                            # เริ่มใหม่ทันที (เก็บ highscore ก่อน)
                            hs = self.highscore
                            self.reset()
                            self.highscore = hs
                            self.state = "playing"
                            # เริ่มเล่นเพลงอีกครั้งถ้ามี
                            try:
                                if self.music_loaded and not pygame.mixer.music.get_busy():
                                    pygame.mixer.music.play(-1)
                            except Exception:
                                pass
                        elif event.key == pygame.K_ESCAPE:
                            self.reset()
                    # Toggle วิธีเล็ง
                    if event.key == pygame.K_m:
                        aim_with_mouse = not aim_with_mouse

            # อัพเดตสถานะเกม
            if self.state == "playing":
                self.update_playing()

            # วาดภาพตาม state
            if self.state == "menu":
                self.draw_menu(screen)
            elif self.state == "playing":
                self.draw_playing(screen)
            elif self.state == "pause":
                self.draw_playing(screen)
                self.draw_pause(screen)
            elif self.state == "gameover":
                self.draw_gameover(screen)

            # ถ้าไม่เล็งด้วยเมาส์ ให้ซ่อนไอคอนเมาส์
            pygame.mouse.set_visible(self.state != "playing" or aim_with_mouse)

            pygame.display.flip()

        # ก่อนจบ ให้หยุดเพลง
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        pygame.quit()


if __name__ == "__main__":
    Game().run()
