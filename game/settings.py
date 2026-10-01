from dataclasses import dataclass, field


@dataclass
class GameSettings:
    master_volume: float = 0.8
    music_enabled: bool = True
    sound_enabled: bool = True
    animations_enabled: bool = True
    fullscreen: bool = False
    animation_speed: float = 1.0

    def to_dict(self):
        return {
            "master_volume": self.master_volume,
            "music_enabled": self.music_enabled,
            "sound_enabled": self.sound_enabled,
            "animations_enabled": self.animations_enabled,
            "fullscreen": self.fullscreen,
            "animation_speed": self.animation_speed,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**(data or {}))
