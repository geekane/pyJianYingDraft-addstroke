"""与模板模式相关的类及函数等"""

from enum import Enum
from copy import deepcopy

from . import util
from .exceptions import ExtensionFailed
from .track import Base_track, Track_type
from .time_util import Timerange
from .local_materials import Video_material, Audio_material

from typing import List, Dict, Any

class Shrink_mode(Enum):
    """处理替换素材时素材变短情况的方法"""

    cut_head = "cut_head"
    """裁剪头部, 即后移片段起始点"""
    cut_tail = "cut_tail"
    """裁剪尾部, 即前移片段终止点"""

    cut_tail_align = "cut_tail_align"
    """裁剪尾部并消除间隙, 即前移片段终止点, 后续片段也依次前移"""

    shrink = "shrink"
    """保持中间点不变, 两端点向中间靠拢"""

class Extend_mode(Enum):
    """处理替换素材时素材变长情况的方法"""

    extend_head = "extend_head"
    """延伸头部, 即尝试前移片段起始点, 与前续片段重合时失败"""
    extend_tail = "extend_tail"
    """延伸尾部, 即尝试后移片段终止点, 与后续片段重合时失败"""

    push_tail = "push_tail"
    """延伸尾部, 若有必要则依次后移后续片段, 此方法总是成功"""

class Imported_segment:
    """导入的视频/音频片段"""

    raw_data: Dict[str, Any]
    """原始数据"""

    material_id: str
    """使用的素材id"""
    source_timerange: Timerange
    """片段取用的素材时间范围"""
    target_timerange: Timerange
    """片段在轨道上的时间范围"""

    __DATA_ATTRS = ["material_id", "source_timerange", "target_timerange"]
    def __init__(self, json_data: Dict[str, Any]):
        self.raw_data = deepcopy(json_data)

        util.assign_attr_with_json(self, self.__DATA_ATTRS, json_data)

    @property
    def start(self) -> int:
        """片段起始时间, 微秒"""
        return self.target_timerange.start
    @start.setter
    def start(self, value: int):
        self.target_timerange.start = value

    @property
    def duration(self) -> int:
        """片段持续时间, 微秒"""
        return self.target_timerange.duration
    @duration.setter
    def duration(self, value: int):
        self.target_timerange.duration = value

    @property
    def end(self) -> int:
        """片段结束时间, 微秒"""
        return self.target_timerange.end

    def export_json(self) -> Dict[str, Any]:
        json_data = deepcopy(self.raw_data)
        json_data.update(util.export_attr_to_json(self, self.__DATA_ATTRS))
        return json_data

class Static_track(Base_track):
    """模板模式下导入的不可修改的轨道"""

    raw_data: Dict[str, Any]
    """原始轨道数据"""

    def __init__(self, json_data: Dict[str, Any]):
        self.track_type = Track_type.from_name(json_data["type"])
        self.name = json_data["name"]
        self.track_id = json_data["id"]
        self.render_index = max([int(seg["render_index"]) for seg in json_data["segments"]])

        self.raw_data = deepcopy(json_data)

    def export_json(self) -> Dict[str, Any]:
        return self.raw_data

class Imported_track(Base_track):
    """模板模式下导入且可修改的轨道"""

    raw_data: Dict[str, Any]
    """原始轨道数据"""
    segments: List[Imported_segment]
    """该轨道包含的片段列表"""

    def __init__(self, json_data: Dict[str, Any]):
        self.track_type = Track_type.from_name(json_data["type"])
        self.name = json_data["name"]
        self.track_id = json_data["id"]
        self.render_index = max([int(seg["render_index"]) for seg in json_data["segments"]])

        self.raw_data = deepcopy(json_data)
        self.segments = [Imported_segment(seg) for seg in json_data["segments"]]

    def __len__(self):
        return len(self.segments)

    @property
    def start_time(self) -> int:
        """轨道起始时间, 微秒"""
        if len(self.segments) == 0:
            return 0
        return self.segments[0].target_timerange.start

    @property
    def end_time(self) -> int:
        """轨道结束时间, 微秒"""
        if len(self.segments) == 0:
            return 0
        return self.segments[-1].target_timerange.end

    def check_material_type(self, material: object) -> bool:
        """检查素材类型是否与轨道类型匹配"""
        if self.track_type == Track_type.video and isinstance(material, Video_material):
            return True
        if self.track_type == Track_type.audio and isinstance(material, Audio_material):
            return True
        return False

    def process_timerange(self, seg_index: int, new_duration: int,
                          shrink: Shrink_mode, extend: List[Extend_mode]) -> None:
        """处理素材替换的时间范围变更"""
        seg = self.segments[seg_index]

        # 时长变短
        delta_duration = abs(new_duration - seg.duration)
        if new_duration < seg.duration:
            if shrink == Shrink_mode.cut_head:
                seg.start += delta_duration
            elif shrink == Shrink_mode.cut_tail:
                seg.duration -= delta_duration
            elif shrink == Shrink_mode.cut_tail_align:
                seg.duration -= delta_duration
                for i in range(seg_index+1, len(self.segments)): # 后续片段也依次前移相应值（保持间隙）
                    self.segments[i].start -= delta_duration
            elif shrink == Shrink_mode.shrink:
                seg.duration -= delta_duration
                seg.start += delta_duration // 2
            else:
                raise ValueError(f"Unsupported shrink mode: {shrink}")
        # 时长变长
        elif new_duration > seg.duration:
            success_flag = False
            prev_seg_end = int(0) if seg_index == 0 else self.segments[seg_index-1].target_timerange.end
            next_seg_start = int(1e15) if seg_index == len(self.segments)-1 else self.segments[seg_index+1].start
            for mode in extend:
                if mode == Extend_mode.extend_head:
                    if seg.start - delta_duration >= prev_seg_end:
                        seg.start -= delta_duration
                        success_flag = True
                elif mode == Extend_mode.extend_tail:
                    if seg.target_timerange.end + delta_duration <= next_seg_start:
                        seg.duration += delta_duration
                        success_flag = True
                elif mode == Extend_mode.push_tail:
                    shift_duration = max(0, seg.target_timerange.end + delta_duration - next_seg_start)
                    seg.duration += delta_duration
                    if shift_duration > 0: # 有必要时后移后续片段
                        for i in range(seg_index+1, len(self.segments)):
                            self.segments[i].start += shift_duration
                    success_flag = True
                else:
                    raise ValueError(f"Unsupported extend mode: {mode}")

                if success_flag:
                    break
            if not success_flag:
                raise ExtensionFailed(f"Failed to extend segment to {new_duration} μs, tried modes: {extend}")

    def export_json(self) -> Dict[str, Any]:
        self.raw_data.update({"segments": [seg.export_json() for seg in self.segments]})
        return self.raw_data