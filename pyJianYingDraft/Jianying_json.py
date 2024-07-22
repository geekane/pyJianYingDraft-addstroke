import os
import json, uuid

from enum import Enum
from typing import Optional, Literal, Union
from typing import Dict, List, Any

from .local_materials import Video_material
from .animation_meta import Video_intro_type, Video_outro_type

class Clip_settings:
    """素材片段的图像调节设置"""

    alpha: float
    """图像透明度, 0-1"""
    flip_horizontal: bool
    """是否水平翻转"""
    flip_vertical: bool
    """是否垂直翻转"""
    rotation: float
    """旋转角度, 可正可负"""
    scale_x: float
    """水平缩放比例"""
    scale_y: float
    """垂直缩放比例"""
    transform_x: float
    """水平位移, 单位为像素?"""
    transform_y: float
    """垂直位移, 单位为像素?"""

    def __init__(self, *, alpha: float = 1.0,
                 flip_horizontal: bool = False, flip_vertical: bool = False,
                 rotation: float = 0.0,
                 scale_x: float = 1.0, scale_y: float = 1.0,
                 transform_x: float = 0.0, transform_y: float = 0.0):
        """初始化图像调节设置, 默认参数表示不作任何图像变换"""
        self.alpha = alpha
        self.flip_horizontal, self.flip_vertical = flip_horizontal, flip_vertical
        self.rotation = rotation
        self.scale_x, self.scale_y = scale_x, scale_y
        self.transform_x, self.transform_y = transform_x, transform_y

    def export_json(self) -> Dict[str, Any]:
        clip_settings_json = {
            "alpha": self.alpha,
            "flip": {"horizontal": self.flip_horizontal, "vertical": self.flip_vertical},
            "rotation": self.rotation,
            "scale": {"x": self.scale_x, "y": self.scale_y},
            "transform": {"x": self.transform_x, "y": self.transform_y}
        }
        return clip_settings_json

class Timerange:
    """记录了起始时间及持续长度的时间范围"""
    start: int
    """起始时间, 单位为微秒"""
    duration: int
    """持续长度, 单位为微秒"""

    def __init__(self, start: int, duration: int):
        self.start = start
        self.duration = duration

    def export_json(self) -> Dict[str, int]:
        return {"start": self.start, "duration": self.duration}

class Keyframe:
    """一个关键帧（关键点）, 目前只支持线性插值"""

    kf_id: str
    """关键帧全局id, 自动生成"""
    time_offset: int
    """相对于素材起始点的时间偏移量"""
    values: List[float]
    """关键帧的值, 似乎一般只有一个元素"""

    def __init__(self, time_offset: int, value: float):
        """给定时间偏移量及关键值, 初始化关键帧"""
        self.kf_id = uuid.uuid4().hex

        self.time_offset = time_offset
        self.values = [value]

    def export_json(self) -> Dict[str, Any]:
        return {
            # 默认值
            "curveType": "Line",
            "graphID": "",
            "left_control": {"x": 0.0, "y": 0.0},
            "right_control": {"x": 0.0, "y": 0.0},
            # 自定义属性
            "id": self.kf_id,
            "time_offset": self.time_offset,
            "values": self.values
        }

class Keyframe_property(Enum):
    """关键帧所控制的属性类型"""

    position_x = "KFTypePositionX"
    position_y = "KFTypePositionY"
    rotation = "KFTypeRotation"

    scale_x = "KFTypeScaleX"
    """单独控制X轴缩放比例"""
    scale_y = "KFTypeScaleY"
    """单独控制Y轴缩放比例"""
    uniform_scale = "UNIFORM_SCALE"
    """同时控制X轴及Y轴缩放比例"""

    alpha = "KFTypeAlpha"
    saturation = "KFTypeSaturation"
    contrast = "KFTypeContrast"
    brightness = "KFTypeBrightness"

class Keyframe_list:
    """关键帧列表, 记录与某个特定属性相关的一系列关键帧"""

    list_id: str
    """关键帧列表全局id, 自动生成"""
    keyframe_property: Keyframe_property
    """关键帧对应的属性"""
    keyframes: List[Keyframe]
    """关键帧列表"""

    def __init__(self, keyframe_property: Keyframe_property):
        """为给定的关键帧属性初始化关键帧列表"""
        self.list_id = uuid.uuid4().hex

        self.keyframe_property = keyframe_property
        self.keyframes = []

    def add_keyframe(self, time_offset: int, value: float):
        """给定时间偏移量及关键值, 向此关键帧列表中添加一个关键帧"""
        keyframe = Keyframe(time_offset, value)
        self.keyframes.append(keyframe)
        self.keyframes.sort(key=lambda x: x.time_offset)

    def export_json(self) -> Dict[str, Any]:
        keyframe_list_json = {
            "id": self.list_id,
            "keyframe_list": [kf.export_json() for kf in self.keyframes],
            "material_id": "",
            "property_type": self.keyframe_property.value
        }
        return keyframe_list_json


class Animation:
    """一个动画效果"""

    name: str
    """动画名称, 默认取为动画效果的名称"""
    effect_id: str
    """另一种动画id, 由剪映本身提供"""
    animation_type: str
    resource_id: str
    """资源id, 由剪映本身提供"""

    start: int
    """动画相对此片段开头的偏移, 单位为微秒"""
    duration: int
    """动画持续时间, 单位为微秒, 各动画有其默认值"""

    category_id: str
    category_name: str

    is_video_animation: bool

    def __init__(self, animation_type: Union[Video_intro_type, Video_outro_type],
                 start: Optional[int] = None, duration: Optional[int] = None):
        type_meta = animation_type.value
        self.name = type_meta.title
        self.effect_id = type_meta.effect_id
        self.resource_id = type_meta.resource_id

        if isinstance(animation_type, Video_intro_type):
            self.animation_type = "in"
            self.category_id = "in"
            self.category_name = "入场"

            if start is None: start = 0
            if duration is None: duration = type_meta.duration
            self.is_video_animation = True
        elif isinstance(animation_type, Video_outro_type):
            self.animation_type = "out"
            self.category_id = "out"
            self.category_name = "出场"

            if duration is None: duration = type_meta.duration
            if start is None: raise ValueError("Outro animation must have a start time")
            self.is_video_animation = True

        self.start = start
        self.duration = duration

    def export_json(self) -> Dict[str, Any]:
        return {
            "anim_adjust_params": None,
            "platform": "all",
            "panel": "video" if self.is_video_animation else "",
            "material_type": "video" if self.is_video_animation else "sticker",

            "name": self.name,
            "id": self.effect_id,
            "type": self.animation_type,
            "resource_id": self.resource_id,
            "category_id": self.category_id,
            "category_name": self.category_name,

            "start": self.start,
            "duration": self.duration,
            # 不导出path和request_id字段
        }

class Segment_animations:
    """附加于某素材上的一系列动画（一般是入场、出场）"""

    animation_id: str
    """动画系列全局id, 自动生成"""
    animation_type: str
    """animation_type字段, 似乎总是'sticker_animation'"""

    animations: List[Animation]
    """动画列表"""

    def __init__(self, animation_type: str = "sticker_animation"):
        self.animation_id = uuid.uuid4().hex
        self.animation_type = animation_type
        self.animations = []

    def add_animation(self, animation: Animation) -> None:
        if animation.animation_type in [ani.animation_type for ani in self.animations]:
            raise ValueError(f"Duplicate animation type '{animation.animation_type}'")
        self.animations.append(animation)

    def export_json(self) -> Dict[str, Any]:
        return {
            "id": self.animation_id,
            "type": self.animation_type,
            "multi_language_current": "none",
            "animations": [animation.export_json() for animation in self.animations]
        }

class Video_segment:
    """安放在轨道上的一个视频/图片片段"""

    segment_id: str
    """片段全局id, 自动生成"""
    material_id: str
    """使用的素材id"""
    source_timerange: Timerange
    """截取的素材片段的时间范围"""
    target_timerange: Timerange
    """片段在轨道上的时间范围"""

    common_keyframes: List[Keyframe_list]
    """各属性的关键帧列表"""
    extra_material_refs: List[str]
    """附加的素材id列表, 用于链接动画等"""
    clip_settings: Clip_settings
    """图像调节设置"""

    uniform_scale: bool
    """是否锁定XY轴缩放比例"""
    animations_instance: Optional[Segment_animations]
    """动画实例, 可能为空"""

    def __init__(self, material: Video_material,
                 target_timerange: Timerange,
                 source_timerange: Optional[Timerange] = None,
                 clip_settings: Optional[Clip_settings] = None):
        """利用给定的视频/图片素材构建一个轨道片段, 并指定其时间信息及图像调节设置

        片段创建完成后, 可通过`Script_file.add_segment`方法将其添加到轨道中

        Args:
            material (`Video_material`): 素材实例, 注意你仍然需要为其调用`Script_file.add_material`来将其添加到素材列表中
            target_timerange (`Timerange`): 片段在轨道上的目标时间范围
            source_timerange (`Timerange`, optional): 截取的素材片段的时间范围, 默认从开头截取与`target_timerange`等长的一部分
            clip_settings (`Clip_settings`, optional): 图像调节设置, 默认不作任何变换
        """
        self.segment_id = uuid.uuid4().hex
        self.material_id = material.material_id

        self.clip_settings = clip_settings if clip_settings is not None else Clip_settings()

        self.common_keyframes = []
        self.extra_material_refs = []
        self.uniform_scale = True
        self.animations_instance = None

        self.target_timerange = target_timerange
        self.source_timerange = source_timerange if source_timerange is not None else Timerange(0, target_timerange.duration)

    def attach_animation(self, animation: Segment_animations) -> None:
        """将给定的动画链接到此片段, 你仍然需要调用`Script_file.add_animation`来将动画添加到素材列表中"""
        assert self.animations_instance is None
        self.animations_instance = animation
        self.extra_material_refs.append(animation.animation_id)

    def add_animation(self, animation_type: Union[Video_intro_type, Video_outro_type]) -> None:
        """将给定的入场/出场动画添加到此片段的动画列表中, 此方法不支持手动调节动画参数"""
        if not isinstance(animation_type, (Video_intro_type, Video_outro_type)):
            raise TypeError("Invalid animation type")
        is_intro = isinstance(animation_type, Video_intro_type)

        if self.animations_instance is None:
            self.animations_instance = Segment_animations()
            self.extra_material_refs.append(self.animations_instance.animation_id)

        self.animations_instance.add_animation(
            Animation(animation_type,
                      start= 0 if is_intro else self.target_timerange.duration - animation_type.value.duration,
                      duration=animation_type.value.duration
        ))

    def add_keyframe(self, _property: Keyframe_property, time_offset: int, value: float):
        """为给定属性创建一个关键帧, 并自动加入到关键帧列表中

        Args:
            _property (`Keyframe_property`): 要控制的属性
            time_offset (`int`): 关键帧的时间偏移量, 单位为微秒
            value (`float`): 属性在`time_offset`处的值

        Raises:
            `ValueError`: 试图同时设置`uniform_scale`以及`scale_x`或`scale_y`其中一者

        """
        if (_property == Keyframe_property.scale_x or _property == Keyframe_property.scale_y) and self.uniform_scale:
            self.uniform_scale = False
        elif _property == Keyframe_property.uniform_scale:
            if not self.uniform_scale: raise ValueError("Cannot set uniform_scale when scale_x or scale_y already exist")
            _property = Keyframe_property.scale_x

        for kf_list in self.common_keyframes:
            if kf_list.keyframe_property == _property:
                kf_list.add_keyframe(time_offset, value)
                return
        kf_list = Keyframe_list(_property)
        kf_list.add_keyframe(time_offset, value)
        self.common_keyframes.append(kf_list)

    def export_json(self) -> Dict[str, Any]:
        fields = {
            # 定义一致字段的默认值
            "caption_info": None,
            "cartoon": False,
            "enable_adjust": True,
            "enable_color_correct_adjust": False,
            "enable_color_curves": True,
            "enable_color_match_adjust": False,
            "enable_color_wheels": True,
            "enable_lut": True,
            "enable_smart_color_adjust": False,
            "group_id": "",
            "hdr_settings": {"intensity": 1.0, "mode": 1, "nits": 1000},
            "intensifies_audio": False,
            "is_placeholder": False,
            "is_tone_modify": False,
            "last_nonzero_volume": 1.0,
            "render_index": 0,
            "responsive_layout": {"enable": False, "horizontal_pos_layout": 0, "size_layout": 0, "vertical_pos_layout": 0, "target_follow": ""},
            "reverse": False,
            "speed": 1.0,
            "template_id": "",
            "template_scene": "default",
            "track_attribute": 0,
            "track_render_index": 0,
            "visible": True,
            "volume": 1.0,
            # 写入自定义字段
            "id": self.segment_id,
            "material_id": self.material_id,
            "common_keyframes": [kf_list.export_json() for kf_list in self.common_keyframes],
            "extra_material_refs": self.extra_material_refs,
            "keyframe_refs": [], # 意义不明
            "source_timerange": self.source_timerange.export_json(),
            "target_timerange": self.target_timerange.export_json(),
            "clip": self.clip_settings.export_json(),
            "uniform_scale": {"on": self.uniform_scale, "value": 1.0},
        }

        return fields

class Script_material:
    """脚本文件中的素材信息部分"""

    videos: List[Video_material]
    """视频素材列表"""

    animations: List[Segment_animations]
    """动画素材列表"""

    def __init__(self):
        self.videos = []
        self.animations = []

    def __contains__(self, item: Union[Video_material, Segment_animations]) -> bool:
        if isinstance(item, Video_material):
            return item.material_id in [video.material_id for video in self.videos]
        elif isinstance(item, Segment_animations):
            return item.animation_id in [ani.animation_id for ani in self.animations]
        else:
            raise TypeError("Invalid argument type '%s'" % type(item))

    def export_json(self) -> Dict[str, List[Any]]:
        return {
            "ai_translates": [],
            "audio_balances": [],
            "audio_effects": [],
            "audio_fades": [],
            "audio_track_indexes": [],
            "audios": [],
            "beats": [],
            "canvases": [],
            "chromas": [],
            "color_curves": [],
            "digital_humans": [],
            "drafts": [],
            "effects": [],
            "flowers": [],
            "green_screens": [],
            "handwrites": [],
            "hsl": [],
            "images": [],
            "log_color_wheels": [],
            "loudnesses": [],
            "manual_deformations": [],
            "masks": [],
            "material_animations": [ani.export_json() for ani in self.animations],
            "material_colors": [],
            "multi_language_refs": [],
            "placeholders": [],
            "plugin_effects": [],
            "primary_color_wheels": [],
            "realtime_denoises": [],
            "shapes": [],
            "smart_crops": [],
            "smart_relights": [],
            "sound_channel_mappings": [],
            "speeds": [],
            "stickers": [],
            "tail_leaders": [],
            "text_templates": [],
            "texts": [],
            "time_marks": [],
            "transitions": [],
            "video_effects": [],
            "video_trackings": [],
            "videos": [video.export_json() for video in self.videos],
            "vocal_beautifys": [],
            "vocal_separations": []
        }

class Script_file:

    content: Dict[str, Any]
    """脚本文件内容"""

    width: int
    """视频的宽度, 单位为像素"""
    height: int
    """视频的高度, 单位为像素"""
    fps: int
    """视频的帧率"""
    duration: int

    materials: Script_material
    """脚本文件中的素材信息部分"""

    TEMPLATE_FILE = "draft_content_template.json"

    def __init__(self, width: int, height: int, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps
        self.duration = 0

        self.materials = Script_material()

        with open(os.path.join(os.path.dirname(__file__), self.TEMPLATE_FILE), "r", encoding="utf-8") as f:
            self.content = json.load(f)

    def add_material(self, material: Video_material):
        self.materials.videos.append(material)

    def add_segment(self, segment: Video_segment):
        self.content["tracks"][0]["segments"].append(segment.export_json())
        self.duration = max(self.duration, segment.target_timerange.start + segment.target_timerange.duration)

        if (segment.animations_instance is not None) and (segment.animations_instance not in self.materials):
            self.add_animation(segment.animations_instance)

    def add_animation(self, animation: Segment_animations):
        self.materials.animations.append(animation)

    def dumps(self) -> str:
        self.content["fps"] = self.fps
        self.content["duration"] = self.duration
        self.content["canvas_config"] = {"width": self.width, "height": self.height, "ratio": "original"}
        self.content["materials"] = self.materials.export_json()
        return json.dumps(self.content, ensure_ascii=False, indent=4)