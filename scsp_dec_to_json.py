#!/usr/bin/env python3
import struct
import simplejson as json
import numpy as np
from collections import defaultdict
class ScspOffsets:
    HEADER_WIDTH        = 22
    HEADER_HEIGHT       = 26
    IK_COUNT            = 54
    SLOTS_COUNT         = 58
    TRANSFORM_COUNT     = 62
    PATH_COUNT          = 66
    SKINS_COUNT         = 70
    EVENTS_COUNT        = 74
    ANIMATIONS_COUNT    = 78
    HASH_PTR            = 82
    SPINE_PTR            = 86
    BONES_COUNT         = 106
class BinaryReader:
    def __init__(self, file_path, initial_pos=0):
        self.file_path = file_path
        self.data = None
        self.pos = initial_pos
        self.strings_data = None
        self.read_file()

    def read_file(self):
        with open(self.file_path, 'rb') as f:
            self.data = f.read()
        
        # 根据 SCSPReader.cs: stringsOffset = ReadInt32() + 8
        self.strings_offset = self.uint32() + 8
        self.strings_length = self.uint32()
        self.strings_data = self.data[self.strings_offset : self.strings_offset + self.strings_length]
    def tell(self): return self.pos
    def seek(self, pos): self.pos = pos
    def skip(self, bytes_count): self.pos += bytes_count
    def unpack(self, fmt, size, read_pos=-1, peek=False):
        if read_pos == -1:
            read_pos = self.pos
        v = struct.unpack(fmt, self.data[read_pos:read_pos+size])[0]
        if not peek:
            self.pos = read_pos + size
        return v
    def int8(self,read_pos = -1,peek=False):
        return self.unpack('<b', 1, read_pos, peek)

    def int16(self,read_pos = -1,peek=False): 
        return self.unpack('<h', 2, read_pos, peek)

    def uint32(self,read_pos = -1,peek=False):
        return self.unpack('<I', 4, read_pos, peek)

    def float32(self,read_pos = -1,peek=False):
        return  self.clean_float(self.unpack('<f', 4, read_pos, peek))

    def string(self,read_pos = -1,peek=False):      
        offset = self.uint32(read_pos,peek)
        return self.get_string(offset)   # 你已有的 get_string

    def bool8(self,read_pos = -1,peek=False):
        if read_pos == -1:
            read_pos = self.pos        
        b = self.data[read_pos]
        #b 等于 \xff 返回 None
        if b == b'\xff':
            return None
        if not peek:
            self.pos = read_pos + 1
        return b == 1
    
    def bool16(self,read_pos = -1,peek=False):
        if read_pos == -1:
            read_pos = self.pos
        b = self.int16(read_pos,peek)
        if b == -1:
            return False
        return b == 1
    
    def bool_foolat32(self,read_pos = -1,peek=False):
        if read_pos == -1:
            read_pos = self.pos
        f = self.float32(read_pos,peek)
        if f == -1:
            return False
        return f == 1
      
    def color(self,read_pos = -1,peek=False,need_alpha=True):
        if read_pos == -1:
            read_pos = self.pos
        r = self.clean_float(self.float32(read_pos,peek))
        g = self.clean_float(self.float32(-1,peek))
        b = self.clean_float(self.float32(-1,peek))
        if need_alpha:
            a = self.clean_float(self.float32(-1,peek))
            return ''.join(f"{int(c * 255):02X}" for c in (r, g, b, a))
        return ''.join(f"{int(c * 255):02X}" for c in (r, g, b))
    @staticmethod
    def clean_float(value, precision=10):
        """
        将浮点数转换为最简数值形式
        - 如果是整数，返回int类型
        - 如果是小数，保留有效精度并去除尾随零
        """
        import math
        # 检查是否为 NaN
        if isinstance(value, float) and math.isnan(value):
            raise ValueError("Value cannot be NaN")
        
        # value 为null 向上抛异常
        if value == 'nan':
            raise ValueError("Value cannot be None")
            
        # 如果本身就是整数值
        if value == int(value):
            return int(value)
        
        # 使用指定精度格式化为字符串，然后转换为 Decimal
        formatted = f"{value:.{precision}f}"
        # 去除尾随零，但保留至少 precision 位小数
        formatted = f"{value:.{precision}f}".rstrip('0').rstrip('.')
        from decimal import Decimal
        return Decimal(formatted) if formatted and '.' in formatted else int(formatted)    
    def get_string(self, offset_in_strings):
        if offset_in_strings >= len(self.strings_data):
            return ""
        # 寻找以 \0 结尾的字符串
        end = self.strings_data.find(b'\x00', offset_in_strings)
        if end == -1:
            return self.strings_data[offset_in_strings:].decode('utf-8', errors='ignore')
        return self.strings_data[offset_in_strings:end].decode('utf-8', errors='ignore')
      
    def find_string_offset(self, target_string):
        """根据输入字符串查找其在字符串数据区中的偏移值"""
        # 将目标字符串编码为字节数组，并加上 null 终止符
        target_bytes = target_string.encode('utf-8') + b'\x00'
        
        # 在字符串数据区中查找该字节序列
        offset = self.strings_data.find(target_bytes)
        
        # 如果找到，返回偏移量；否则返回 -1 表示未找到
        return offset if offset != -1 else -1

    def find_all_string_offsets(self, target_string):
        """根据输入字符串查找其在字符串数据区中的所有匹配偏移值"""
        # 将目标字符串编码为字节数组，并加上 null 终止符
        target_bytes = target_string.encode('utf-8') + b'\x00'
        
        offsets = []
        start = 0
        
        # 循环查找所有匹配项
        while True:
            # 从当前位置开始查找该字节序列
            offset = self.strings_data.find(target_bytes, start)
            
            # 如果没有找到更多匹配项，跳出循环
            if offset == -1:
                break
                
            # 添加找到的偏移量到结果列表
            offsets.append(offset)
            
            # 更新下一次搜索的起始位置
            start = offset + 1
        
        # 返回所有找到的偏移量列表
        return offsets
class ScspParser:
    def __init__(self,reader:BinaryReader):
        self.reader = reader
        self.data = None
        self.bones_lookup = {}  # 记录索引到名称的映射，供Slot使用
        self.transform_lookup = {}
        self.path_lookup = {}
        self.slots_lookup = {}
        self.slots_name_attachment_map = {}
        self.ik_lookup = {}
        self.solts_list = []
        self.solts_name_list = []
        self.events_lookup = {}
        self.events = {}
        self.skins = {}
        self.skins_lookup = {}
        
        
        
    

    @staticmethod
    def hex_curve(hex_data):
        data = hex_data  # hex_data已经是字节数据，不需要转换
        floats = np.frombuffer(data, dtype=np.dtype('<f4'))  # 小端序 float32
        # 转为 (x, y) 点列表
        points = floats.reshape(-1, 2)
        return points
    def calculate_curve_params(self,points, curve_type_hex=None):
        """
        从hex_curve返回的点数据中计算c1、c2、c3、c4值
        points: 通过hex_curve方法得到的9个点的数组，代表贝塞尔曲线的采样点，每点为(x, y)
        curve_type_hex: 前4个字节的十六进制字符串，表示曲线类型（可选，但推荐传入以区分类型）
        """
        import numpy as np
        
        if curve_type_hex:
            # 特殊值处理（基于Spine的float表示）
            if curve_type_hex == b'\x00\x00\x80\x3f':  # 1.0 - stepped
                # return {"c1": 0, "c2": 0, "c3": 0, "c4": 1}  # 或自定义stepped表示
                return {"curve" : "stepped"}
            elif curve_type_hex == b'\x00\x00\x00\x00':  # 0.0 - linear（视Spine实现而定，有时用0表示linear）
                return {"curve": 0, "c2": 0, "c3": 1, "c4": 1}
            # 如果是'40000000' (2.0) 或其他，继续贝塞尔拟合
        
        # 以下为贝塞尔拟合逻辑（假设默认或已确认是贝塞尔）
        if len(points) != 9:
            return None
        
        xs = np.array([p[0] for p in points])
        ys = np.array([p[1] for p in points])
        
        t_values = np.linspace(0.1, 0.9, 9)
        
        A = np.zeros((9, 2))
        b_x = xs - t_values**3
        
        for i, t in enumerate(t_values):
            A[i, 0] = 3 * (1 - t)**2 * t
            A[i, 1] = 3 * (1 - t) * t**2
        
        try:
            cx1, cx2 = np.linalg.lstsq(A, b_x, rcond=None)[0]
        except:
            return None
        
        b_y = ys - t_values**3
        
        try:
            cy1, cy2 = np.linalg.lstsq(A, b_y, rcond=None)[0]
        except:
            return None
        
        cx1 = np.clip(cx1, 0.0, 1.0)
        cx2 = np.clip(cx2, 0.0, 1.0)
        cy1 = np.clip(cy1, 0.0, 1.0)
        cy2 = np.clip(cy2, 0.0, 1.0)
        
        deviations = np.abs(ys - xs)
        avg_deviation = np.mean(deviations)
        is_linear = (abs(cx1) < 0.01 and abs(1 - cx2) < 0.01 and 
                     abs(cy1) < 0.01 and abs(1 - cy2) < 0.01) or avg_deviation < 0.01
        
        # if is_linear:
        #     return {"curve": 0, "c2": 0, "c3": 1, "c4": 1}
        return {
            "curve":self.reader.clean_float(float(cx1),6),
            "c2":self.reader.clean_float(float(cy1),6),
            "c3": self.reader.clean_float(float(cx2),6),
            "c4": self.reader.clean_float(float(cy2),6)
        }
    def parse_skeleton_info(self):
        reader = self.reader
        width = reader.float32(ScspOffsets.HEADER_WIDTH)
        height = reader.float32(ScspOffsets.HEADER_HEIGHT)
        hash = reader.string(ScspOffsets.HASH_PTR)
        spine = reader.string(ScspOffsets.SPINE_PTR)
        return {
            "spine": spine,
            "x": 0, "y": 0,
            "width": round(width, 2),
            "height": round(height, 2),
            "hash": hash,
        }       
    def parse_bones(self):
        """解析骨骼 (恢复 round(val, 2)，并补全缺失参数)"""
        bones = []
        # Bones区域起始于 106
        reader = self.reader
        bones_count = reader.int16(ScspOffsets.BONES_COUNT)
        print (f"--- 骨骼数量: {bones_count} ---")
        for i in range(bones_count):
            bone_id = reader.int16()
            name = reader.string()
            
            self.bones_lookup[i] = name 
            parent_id = reader.int16()
            length = reader.float32()
            x = reader.float32()
            y = reader.float32()
            rotation = reader.float32()
            scale_x = reader.float32()
            scale_y = reader.float32()
            shear_x = reader.float32()
            shear_y = reader.float32()
            transform_mode = reader.int8()
            skin_required = reader.bool8()
            reader.skip(1)

            bone_data = {"name": name}
            
            # 只有非 root 骨骼才写 parent
            if parent_id != -1:
                bone_data["parent"] = self.bones_lookup.get(parent_id, "root")
            
            # 补全 length 字段
            if abs(length) > 0.001:
                bone_data["length"] = length
            if abs(x) > 0.001: bone_data["x"] = x
            if abs(y) > 0.001: bone_data["y"] = y
            if abs(rotation) > 0.001: bone_data["rotation"] = rotation
            if abs(float(scale_x) - 1.0) > 0.001: bone_data["scaleX"] = scale_x
            if abs(float(scale_y) - 1.0) > 0.001: bone_data["scaleY"] = scale_y
            if abs(float(shear_x)) > 0.001: bone_data["shearX"] = shear_x
            if abs(float(shear_y)) > 0.001: bone_data["shearY"] = shear_y
            # 映射 transform，确保默认值 normal 也被写入
            mode_map = {
                0: "normal",
                1: "onlyTranslation", 
                2: "noRotationOrReflection", 
                3: "noScale", 
                4: "noScaleOrReflection"
            }
            bone_data["transform"] = mode_map.get(transform_mode, "normal")
            
            if skin_required:
                bone_data["skin"] = True
                
            bones.append(bone_data)
        reader.skip(2)
        return bones
    def parse_ik(self):
            reader = self.reader
            ik_count = reader.int16(ScspOffsets.IK_COUNT,True)
            ik = []
            for i in range(ik_count):
                name = reader.string()
                # Name (StringRef/Pointer)
                self.ik_lookup[i] = name
                order = reader.int16()
                reader.skip(3)
                bendPositive = reader.bool16()
                reader.skip(2)
                #TODOcompress和 stretch 有关系 但是现在无法分辨
                compress = reader.bool16()
                reader.skip(7)
                stretch = reader.bool16()
                target_bone_id = reader.int16()
                target = self.bones_lookup.get(target_bone_id)
                bone_count = reader.int16()
            
                

                #TODO 这里mix 和 softness 没有找到不同的字段，先忽略
                mix = 1
                softness = 0

                # Bone IDs (Count + IDs)
                bones = []
                for i in range(bone_count):
                    bone_id = reader.int16()
                    bones.append(self.bones_lookup.get(bone_id))

           

                ik_data = {
                    "name": name,
                    "order": order,
                    "bones": bones,
                    "target": target,
                    "mix": mix,
                    "softness": softness,
                    "bones": bones,
                }
                if(bendPositive != None):
                    ik_data["bendPositive"] = bendPositive
                if(compress != False):
                    ik_data["compress"] = compress
                if(stretch != False):
                    ik_data["stretch"] = stretch
                ik.append(ik_data)

                #
            print(f"所有约束跳过完成，当前指针: {reader.pos}，即将开始解析 Slots")
            return ik
    def parse_slots(self):
        """
        根据C#代码逻辑解析slots
        """
        
        slots = []
        
        reader = self.reader
        
        slots_count = reader.int16(ScspOffsets.SLOTS_COUNT,True)
        reader.skip(2)
        for i in range(slots_count):
            test = reader.int16()
            # 读取slot名称引用 (4字节)
            slot_name = reader.string()
            bone_id = reader.int16()
            self.slots_lookup[i] = slot_name
            color = reader.color()
            darkColor = reader.color()
            reader.skip(1)  # 跳过未知数据
            
            attachment = reader.string()
            blend_mode = reader.int16()
            bone_name = self.bones_lookup.get(bone_id, "root")  # 默认为root
            
            # 创建slot数据对象
            slot_data = {
                "name": slot_name,
                "bone": bone_name,
                 # 默认attachment和slot名称相同
            }
            if color != "FFFFFFFF": 
                slot_data["color"] = color     
            if darkColor != "FFFFFFFF" and darkColor != "00000000":   
                #移除最后FF字符
                if len(darkColor) >= 2 and darkColor.endswith("FF"):
                    darkColor = darkColor[:-2]
                slot_data["darkColor"] = darkColor
            if attachment != "":            
                slot_data["attachment"] = attachment
            if self.slots_name_attachment_map.get(attachment)  == None:               
                self.slots_name_attachment_map[attachment] = slot_name
            self.solts_name_list.append(slot_name)
            # 处理blend模式
            if blend_mode != 0:  # 不是normal blend
                blend_map = {1: "additive", 2: "multiply", 3: "screen"}
                slot_data["blend"] = blend_map.get(blend_mode, "normal")
            
            slots.append(slot_data)
            
        return slots

    def parse_transform(self):
        reader = self.reader
        transform_count = reader.int16()  # 读取transform数量
        transform = []
        
        for i in range(transform_count):
            # 读取名称引用 (4字节)
            name = reader.string()
            self.transform_lookup[i] = name
            
            order = reader.int16()
            skin = reader.bool8()
            reader.skip(2)
            # 读取旋转相关数据
            rotateMix = reader.float32()
            translateMix = reader.float32()
            scaleMix = reader.float32()
            shearMix = reader.float32()
            
            # 读取变换数据
            rotation = reader.float32()
            x = reader.float32()
            y = reader.float32()
            scaleX = reader.float32()
            scaleY = reader.float32()
            shearY = reader.float32()
            relative = reader.bool8()
            local = reader.bool8()
            target_bone_id = reader.int16()
            target = self.bones_lookup.get(target_bone_id)
            bone_count = reader.int16()
            
        
            bones = []
            for j in range(bone_count):
                bone_id = reader.int16()
                bones.append(self.bones_lookup.get(bone_id))
            
            transform_data = {
                "name": name,
                "order": order,
                "skin": skin,
                "target": target,
                "bones": bones,
                "rotateMix": rotateMix,
                "translateMix": translateMix,
                "scaleMix": scaleMix,
                "shearMix": shearMix,
                "rotation": rotation,
                "x": x,
                "y": y,
                "scaleX": scaleX,
                "scaleY": scaleY,
                "shearY": shearY,
                "relative": relative,
                "local": local,
            }
            transform.append(transform_data)
            
        return transform
    def parse_path(self):
        spacing_mode_map = {
            0:"length",
            1:"fixed",
            2:"percent",
            3:"proportional"
        }
        rotate_mode_map = {
            0:"tangent",
            1:"chain",
            2:"chainScale"
        }
        reader = self.reader
        path_count = reader.int16()
        paths = []
        for i in range(path_count):
            name = reader.string()
            order = reader.int16()
            skin = reader.bool8()
            reader.skip(2)
            position_mode = "fixed" if reader.int16() == 0 else "percent"
            spacing_mode = spacing_mode_map.get(reader.int16())
            rotate_mode = rotate_mode_map.get(reader.int16())
            rotation = reader.float32()
            position =  reader.float32()
            spacing = reader.float32()
            rotateMix = reader.float32()
            translateMix = reader.float32()
            
            target_slot_id = reader.int16()
            target = self.slots_lookup.get(target_slot_id)
            bones_count = reader.int16()
            bones = []
            for j in range(bones_count):
                bone_id = reader.int16()
                bones.append(self.bones_lookup.get(bone_id))
            self.path_lookup[i] = name
            path_data = {
                "name": name,
                "order": order,
                "skin": skin,
                "positionMode": position_mode,
                "spacingMode": spacing_mode,
                "rotateMode": rotate_mode,
                "rotation": rotation,
                "position": position,
                "spacing": spacing,
                "rotateMix": rotateMix,
                "translateMix": translateMix,
                "target": target
            }
            path_data["bones"] = bones
            
            paths.append(path_data)
        return paths
    def vertices(self):
        reader = self.reader
        vertices = []
        vertexCount = 0

        bone_info_count = reader.int16()
        curr_coord_weight = reader.pos + bone_info_count * 2
        coord_weight_count = reader.int16(curr_coord_weight,True)
        bone_info_list = []
        #先整理骨骼数量 和索引信息
        count = 0
        for i in range(bone_info_count):
            bone_count = reader.int16()
            bone_info_list.append(bone_count)
            vertexCount += 1 
            for j in range(bone_count):
                bone_id = reader.int16()
                bone_info_list.append(bone_id)
                
            count += bone_count + 1
            if(count >= bone_info_count):
                break
        
        reader.skip(2)
        bone_info_index = 0
        while bone_info_index < len(bone_info_list):
            bone_count = bone_info_list[bone_info_index]
            bone_info_index += 1
            vertices.append(bone_count)
            
            for j in range(bone_count):
                bone_id = bone_info_list[bone_info_index]
                bone_info_index += 1
                x = reader.float32()
                y = reader.float32()
                weight = reader.float32()
                vertices.extend([bone_id, x, y, weight])
        if bone_info_count == 0 and coord_weight_count != 0:
            vertexCount = int(coord_weight_count / 2)
            for i in range(coord_weight_count):
                vertices.append(reader.float32())  
        return vertices, vertexCount
    def parse_skins(self):
        attachments_type_map = {
                0:"region",
                1:"boundingbox",
                2:"mesh",
                3:"linkedmesh",
                4:"path",
                5:"point",
                6:"clipping"
            }
        reader = self.reader
        # 读取 skins 数量
        skins_count = reader.int16()
        skins = []

        for k in range(skins_count):
            name = reader.string()
            # 跳过奇怪的小区域
            skip_count = reader.int16()
            reader.skip(2 + skip_count*2)
            attachments_count = reader.int16()
            attachments = {}
            self.skins_lookup[k] = name
            skin = {"name": name, "attachments": attachments}
            for j in range(attachments_count):
                solt_id = reader.int16()
                attachment_name = self.slots_lookup.get(solt_id)
                value =  reader.string()
                type_id = reader.int8()
                # print(f"开始解析 Skin {k} 的 Attachment {j} attachment_name: {attachment_name}  type_id:{type_id}")
                type = attachments_type_map.get(type_id, "mesh")
                
                
                reader.skip(1)
                path_ptr = reader.uint32()
                path = reader.get_string(path_ptr)
                # unknown_count = 0
                # if type == "mesh" or type == "linkedmesh":
                #     #TODO未知区域
                #     unknown_count = reader.int16()
                
                
                vertices = []
                vertexCount = 0
                if type != "region":
                    # reader.skip(2)
                    vertices, vertexCount = self.vertices()

                
                if attachments.get(attachment_name) == None:
                    attachments[attachment_name] = {value: {}}
                else: 
                    attachments[attachment_name][value] = {}
                attachments[attachment_name][value]["type"] = type
                
                
                if type == "boundingbox":
                    attachments[attachment_name][value]["vertexCount"] = vertexCount
                    attachments[attachment_name][value]["vertices"] = vertices 
                    attachments[attachment_name][value]["path"] = path
                    reader.skip(4)
                    reader.skip(4)
                elif type == "path":
                    reader.skip(8)
                    lengths_count = reader.int16()
                    lengths = []
                    for i in range(lengths_count):
                        length = reader.float32()
                        lengths.append(length)
                    closed = reader.bool8()
                    constantSpeed = reader.bool8()
                    attachments[attachment_name][value]["closed"] = closed
                    attachments[attachment_name][value]["constantSpeed"] = constantSpeed
                    attachments[attachment_name][value]["lengths"] = lengths
                    attachments[attachment_name][value]["vertices"] = vertices
                    attachments[attachment_name][value]["vertexCount"] = vertexCount
                    attachments[attachment_name][value]["path"] = str(path)
                elif type == "region":
                    x = reader.float32()
                    y = reader.float32()
                    rotation = reader.float32()
                    scale_x = reader.float32()
                    scale_y = reader.float32()
                    width = reader.float32()
                    height = reader.float32()

                    attachments[attachment_name][value]["x"] = x
                    attachments[attachment_name][value]["y"] = y
                    attachments[attachment_name][value]["rotation"] = rotation
                    attachments[attachment_name][value]["scaleX"] = scale_x
                    attachments[attachment_name][value]["scaleY"] = scale_y
                    attachments[attachment_name][value]["width"] = width
                    attachments[attachment_name][value]["height"] = height
                    reader.skip(6)
                    reader.skip(86)
                    path = reader.string()
                    attachments[attachment_name][value]["path"] = str(path)
                    color = reader.color()
                    if color != "FFFFFFFF":
                        attachments[attachment_name][value]["color"] = color 
                elif type == "clipping":
                    reader.skip(8)
                    end_slot_id =  reader.int16()
                    attachments[attachment_name][value]["end"] = self.slots_lookup.get(end_slot_id)
                    attachments[attachment_name][value]["vertices"] = vertices
                    attachments[attachment_name][value]["vertexCount"] = vertexCount
                    attachments[attachment_name][value]["path"] = str(path)   
                elif type == "mesh" or type == "linkedmesh": 
                    unknown_count = reader.int16()
                    reader.skip(unknown_count * 4 + 4 * 6 + 8)
                    uvs = []
                    uvs_count = reader.int16()
                    for i in range(uvs_count):
                        uv = reader.float32()
                        uvs.append(uv)

                    triangles = []
                    triangles_count = reader.int16()
                    for i in range(triangles_count):
                        triangle = reader.int16()
                        triangles.append(triangle)
                    edges_count = reader.int16()
                    edges = []
                    for i in range(edges_count):
                        edge = reader.int16()
                        edges.append(edge)
                    path = reader.string()
                    reader.skip(16)
                    width = reader.float32()#TODO
                    height = reader.float32()#TODO
                    color = reader.color()
                    hull = reader.int16()
                    attachments[attachment_name][value]["uvs"] = uvs    
                    attachments[attachment_name][value]["triangles"] = triangles    
                    attachments[attachment_name][value]["vertices"] = vertices
                    attachments[attachment_name][value]["hull"] = hull    
                    attachments[attachment_name][value]["edges"] = []  
                    attachments[attachment_name][value]["width"] = width    
                    attachments[attachment_name][value]["height"] = height   
                    attachments[attachment_name][value]["path"] = str(path)
                    if color != "FFFFFFFF":
                        attachments[attachment_name][value]["color"] = color   
                    #TODO 奇怪的数据 读reader.data[reader.pos+14:reader.pos+18].hex() 等于ffffff00 则跳过2字节 然后再跳过16字节
                    hex = reader.data[reader.pos+14:reader.pos+18].hex()
                    hex1 = reader.data[reader.pos:reader.pos+2].hex()
                    if hex == 'ffffff00':
                        reader.skip(2)
                    if hex1 == '0000':
                        reader.skip(16)

                else:
                    print()
            skins.append(skin)
        return skins
    def linetime(self,type_id):
        reader = self.reader
            
        count = reader.int16()
        list = []
        for_conut = 0
        while(for_conut < count):
            e = {}
            time = reader.float32()
            e['time'] = time
            if(type_id == 1 or type_id == 2 or type_id == 3):
                e['x'] = reader.float32()
                e['y'] = reader.float32()
                for_conut += 3
            elif(type_id == 0):
                e['angle'] = reader.float32()
                for_conut += 2
            elif(type_id == 11 or type_id == 12):
                e['position'] = reader.float32() 
                for_conut += 2
            elif(type_id == 14):
                e['light'] = reader.color()
                e['dark'] = reader.color(need_alpha=False)
                for_conut += 8
            elif(type_id == 10):
                e['rotateMix'] = reader.float32()
                e['translateMix'] = reader.float32()
                e['scaleMix'] = reader.float32()
                e['shearMix'] = reader.float32()
                for_conut += 5
            elif(type_id == 9):
                e['mix'] = reader.float32()
                e['softness'] = reader.float32()
                reader.skip(4)
                e['bendPositive'] = reader.float32()
                e['stretch'] = reader.float32()
                for_conut += 6
            elif(type_id == 13):
                e['rotateMix'] = reader.float32()
                e['translateMix'] = reader.float32()
                for_conut += 3
            else:
                for_conut += 1
            list.append(e)
        curve_count = reader.int16()
        if curve_count != 0 and type_id != 8:
            curve_for_count = 0
            for j in list:
                if curve_for_count >= len(list) - 1:
                    break
                curve_type = reader.data[reader.pos:reader.pos+4]
                reader.skip(4)
                # 使用通用曲线计算方法
                curve_data = reader.data[reader.pos:reader.pos+72]
                curve_p = self.hex_curve(curve_data)
                reader.skip(72)
                curve_params = self.calculate_curve_params(curve_p, curve_type)
                if curve_params != {"curve": 0, "c2": 0, "c3": 1, "c4": 1}:
                    j.update(curve_params)
                curve_for_count += 1
     
        if(type_id == 6):
            count = reader.int16()
            for i in range(count):
                k = list[i]
                offset = reader.int16() * 4
                offset_count = 0

                offset_num = 0
                while reader.uint32(-1,True) == 0:
                    reader.skip(4)
                    offset_num += 4
                    offset_count += 4
                    
                vertices = []
                while offset_count < offset:
                    # e10bd3bd
                    v = reader.float32()
                    offset_count += 4
                    vertices.append(v)
                    #判断self.data[curr:curr+offset-offset_count] 是否全部为 00 (代表0)) 都为0 则结束
                    if reader.data[reader.pos:reader.pos+offset-offset_count] == b'\x00' * (offset-offset_count):
                        reader.skip (offset - offset_count)
                        break
                re_oder = {
                    "time": k.get('time')
                }        
                if vertices != []:    
                    k['vertices'] = vertices
                    re_oder['vertices'] = vertices
                    if offset % 4 == 0 and offset_num // 4 != 0:
                        k['offset'] = offset_num // 4
                        re_oder['offset'] = offset_num // 4
                if k.get('curve') != None:
                    re_oder['curve'] = k.get('curve')
                if k.get('c2') != None:
                    re_oder['c2'] = k.get('c2')
                if k.get('c3') != None:
                    re_oder['c3'] = k.get('c3')
                if k.get('c4') != None:
                    re_oder['c4'] = k.get('c4')
                list[i] = re_oder
                
            key_ptr = reader.uint32()   
            key = reader.get_string(key_ptr)
            skin_id = reader.int16(peek = True)
            #TODO 这里有点问题 需要确认skin_id是否有效
            if len(self.skins) < skin_id:
                skin_id = 0
            else:
                reader.skip(2)
            return skin_id,{key: list}
        if(type_id == 8):
            for  k in list:
                draw_order_count = reader.int16()
                # offset = reader.int16()
                count = 0
                offsets = []
                offsets_index = []
                for i in range(draw_order_count):
                    index = reader.int16()
                    reader.skip(2)
                    offsets_index.append(index)
                    count += 1
                for i in range(draw_order_count):
                    #从 offsets_index 查找 i 处于列表的那个位置
                    index = offsets_index.index(i)                
                    if i != index:
                        offsets.append({"slot": self.slots_lookup.get(i), "offset": index-i})
                    k["offsets"] = offsets
        return list
    def parse_events(self):
        reader = self.reader
        events_count = reader.int16(74,True)
        # events_count = reader.int16()
        reader.skip(2)
        events = {}
        for i in range(events_count):
            event = {}
            
            name = reader.string()
            int_value = reader.int16()
            float_value = reader.float32()
            reader.skip(2)
            string = reader.string()
            audio = reader.string()
            event["int"] = int_value
            event["float"] = float_value
            event["string"] = string
            if(audio != ""):
                event["audio"] = audio    
            if(audio != ""):
                volume = reader.float32()
                balance = reader.float32()
                event["volume"] = volume
                event["balance"] = balance
            else:
                reader.skip(8)
            events[name] = event
            self.events_lookup[i] = name
        return events
    def parse_animations(self):
        reader = self.reader
        amimations_count = reader.int16()
        animations = {}
        for i in range(amimations_count):
            key = reader.string()
            duration = reader.float32()
            linetime_num =  reader.int16()                     
            slots = {}
            bones = {}
            # 使用嵌套的defaultdict来支持多层访问
            from collections import defaultdict
            deform = defaultdict(lambda: defaultdict(dict))
            drawOrder = []
            events = []
            paths = {}
            transforms = defaultdict(lambda: defaultdict(dict))
            iks = {}
            linetime_count = 0                
            while(linetime_count < linetime_num):
                type_id = reader.int16()
                bones_id = reader.int16(-1,True)
                name = None
                if type_id != 7 and type_id != 8:
                    reader.skip(2)
                if type_id == 4 or type_id == 5 or type_id == 14:
                    name = self.slots_lookup.get(bones_id)
                    if slots.get(name) == None:
                        slots[name] = {}
                elif(type_id == 6):
                    name = self.slots_lookup.get(bones_id)
                elif(type_id == 9):
                    name = self.ik_lookup.get(bones_id)
                elif(type_id == 10):
                    name = self.transform_lookup.get(bones_id)
                    # if transforms.get(name) == None:
                    #     transforms[name] = []
                elif(type_id == 11) or type_id == 13 or type_id ==12: 
                    name = self.path_lookup.get(bones_id)
                    if paths.get(name) == None:
                        paths[name] = {}
                elif (type_id == 0 or type_id == 1 or type_id == 2 or type_id == 3 ):
                    name = self.bones_lookup.get(bones_id)
                    if bones.get(name) == None:
                        bones[name] = {}
                    
                # print(f"bones_name: {name}, type_id: {type_id} , type_count: {linetime_count} , key: {key}")
                if(type_id == 0):
                    bones[name]["rotate"] = self.linetime(type_id)
                    linetime_count += 1
                    continue
                elif(type_id == 1):
                    bones[name]["translate"] = self.linetime(type_id)
                    linetime_count += 1
                    continue
                elif(type_id == 2):                    
                    bones[name]["scale"] = self.linetime(type_id)
                    linetime_count += 1
                    continue
                elif(type_id == 3):
                    bones[name]["shear"] = self.linetime(type_id)
                    linetime_count += 1
                    continue
                elif(type_id == 4):
                    frame_count = reader.int16()
                    attachment = []
                    for k in range(frame_count):
                        tiem = reader.float32()
                        attachment.append({"time": tiem,})
                    count = reader.int16()
                    for k in attachment:
                        slot_name = reader.string()
                        k["name"] = slot_name if slot_name != '' else None 
                    if slots[name].get("attachment") != None:
                        old = slots[name]["attachment"]
                        old.extend(attachment)
                    else:
                        slots[name]["attachment"] = attachment    
                    linetime_count += 1
                    continue
                elif(type_id == 5):
                    frame_count = reader.int16()
                    colors = []
                    for k in range(int(frame_count/5)):
                        time = reader.float32()
                        color = reader.color()
                        colors.append({"time": time,"color": color})
                    reader.skip(2)
                    count = 0
                    for color in colors:
                        if count == len(colors) - 1:
                            break
                        curve_type = reader.data[reader.pos:reader.pos+4]
                        reader.skip(4)
                        curve_data = reader.data[reader.pos:reader.pos+72]
                        curve_p = self.hex_curve(curve_data)
                        reader.skip(72)
                        curve_params = self.calculate_curve_params(curve_p, curve_type)
                        if curve_params != {"curve": 0, "c2": 0, "c3": 1, "c4": 1}:
                            color.update(curve_params)
                        count += 1
                    slots[name]["color"] = colors
                    linetime_count += 1
                    continue
                elif(type_id == 6):
                    skin_id,map = self.linetime(type_id)
                    for k in map.keys():
                        v = map[k]
                        vertices =  self.skins[skin_id]["attachments"][name][k]["vertices"]
                        for e in v:
                            zero_count = 0
                            new_vertices = e.get("vertices")
                            if new_vertices == None:
                                continue
                            if len(vertices) != len(new_vertices):
                                continue
                            for i in range(len(new_vertices)):
                                value =   reader.clean_float(new_vertices[i] - vertices[i])
                                new_vertices[i] = value   
                                if value == 0:
                                    zero_count += 1
                            if zero_count == len(new_vertices):
                                #删除vertices
                                e.pop("vertices")
                            
                    attachment_name = self.skins_lookup.get(skin_id)
                    if deform[attachment_name].get(name) != None:
                        deform[attachment_name][name].update(map)
                    else:
                        deform[attachment_name][name] = map
                    linetime_count += 1
                    continue
                elif(type_id == 7):
                    events_count = reader.int16()
                    list = []
                    for i in range(events_count):
                        #TODO
                        event = {}
                        time = reader.float32()
                        event["time"] = time
                        list.append(event)
                    reader.skip(2)  
                    for e in list:
                        event_name = reader.string()                        
                        e["name"] = event_name
                        events.append(event)
                    events = list
                    linetime_count += 1
                    continue
                elif(type_id == 8):
                    drawOrder = self.linetime(type_id)
                    linetime_count += 1
                    continue
                elif(type_id == 9):
                    ik = self.linetime(type_id)
                    linetime_count += 1
                    iks[name] = ik
                    continue
                elif(type_id == 10):
                    transform = self.linetime(type_id)
                    transforms[name] = transform
                    linetime_count += 1
                    continue          
                elif(type_id == 11):
                    path = self.linetime(type_id)
                    paths[name]["position"] = path
                    linetime_count += 1
                    continue
                elif(type_id == 12):
                    path_spacing = self.linetime(type_id)
                    paths[name]["spacing"] = path_spacing
                    linetime_count += 1
                    continue
                elif(type_id == 13):   
                    path_mix = self.linetime(type_id)   
                    paths[name]["mix"] = path_mix 
                    linetime_count += 1
                    continue                    
                elif(type_id == 14):
                    two_color = self.linetime(14)
                    slots[name]["twoColor"] = two_color
                    linetime_count += 1
                    continue
                break
                
            animations[key] = {
                "bones":bones,
                "slots":slots, 
                "ik":iks, 
                "transform": transforms,
                "path": paths,
                "deform": deform,
                }
            if len(drawOrder) != 0:
                animations[key]["drawOrder"] = drawOrder
            animations[key]["duration"] = duration
            if len(events) != 0:
                animations[key]["events"] = events
            if len(paths) != 0:
                animations[key]["path"] = paths
            
        return animations

    def parse(self):
        skeleton_info = self.parse_skeleton_info()
        #判断spine和hash有一项是否为空 直接抛出错误 不支持的版本
        if len(skeleton_info) == 0 or len(skeleton_info["hash"]) == 0:
            raise Exception("Unsupported version")
        print(f"skeleton_info length: {len(skeleton_info)}")
        bones = self.parse_bones()
        print(f"bones length: {len(bones)}")
        ik = self.parse_ik()
        print(f"ik length: {len(ik)}")
        slots = self.parse_slots()
        print(f"slots length: {len(slots)}")
        self.solts_list = slots
        transform = self.parse_transform()
        print(f"transform length: {len(transform)}")
        path = self.parse_path()
        print(f"path length: {len(path)}")
        skins = self.parse_skins()
        print(f"skins length: {len(skins)}")
        self.skins = skins
        events = self.parse_events()
        print(f"events length: {len(events)}")
        self.events = events
        animations = self.parse_animations()
        print(f"animations length: {len(animations)}")
        print()   
        return {
            "skeleton": skeleton_info,
            "slots": slots,
            "skins": skins,
            "bones": bones,
            "ik": ik,
            "transform": transform,
            "path":path,
            "events": events,
            "animations": animations, 
        }


def batch_convert_decompressed_files(directory_path, extension='scsp'):
    """
    批量转换指定目录下的所有指定扩展名文件为JSON格式
    :param directory_path: 包含指定扩展名文件的目录路径
    :param extension: 要查找的文件扩展名，默认为.scsp
    """
    import os
    import glob
    extension = f".{extension.lstrip('.')}"  # 确保扩展名前有点号
    # 查找目录下所有指定扩展名的文件，包括子目录
    target_files = []
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.lower().endswith(extension.lower()):
                target_files.append(os.path.join(root, file))
    
    if not target_files:
        print(f"在目录 {directory_path} 及其子目录中未找到 {extension} 文件")
        return
    
    print(f"找到 {len(target_files)} 个 {extension} 文件")
    
    # 创建错误记录列表
    error_records = []
    
    for input_file in target_files:
        try:
            print(f"正在处理: {input_file}")
            
            # 创建输出JSON文件名 - 保持原有逻辑，但保留相对路径结构
            # 获取相对于输入目录的路径
            rel_path = os.path.relpath(input_file, directory_path)
            # 处理文件名 - 去掉指定扩展名以及之前的所有扩展名部分
            base_name = os.path.basename(rel_path)
            dir_name = os.path.dirname(rel_path)
            
            # 只去掉指定扩展名后缀
            if base_name.lower().endswith(extension.lower()):
                base_name = base_name[:-len(extension)]
                # 如果仍然包含点号，则只保留第一个点号之前的部分
                if '.' in base_name:
                    base_name = base_name.split('.')[0]
            
            # 构建输出路径，保持原有的子目录结构
            output_json = os.path.join(directory_path, dir_name, f"{base_name}.json")
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_json)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # 解析文件
            reader =  BinaryReader(input_file)
            parser = ScspParser(reader)
            result = parser.parse()
            
            # 将 numpy 类型转换为 Python 原生类型，以便 JSON 序列化
            def convert_numpy_types(obj):
                import numpy as np
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()  # 转换为 Python 列表
                elif isinstance(obj, list):
                    return [convert_numpy_types(item) for item in obj]
                elif isinstance(obj, dict):
                    return {key: convert_numpy_types(value) for key, value in obj.items()}
                else:
                    return obj

            result = convert_numpy_types(result)
            
            # 写入JSON文件
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(result, f,ensure_ascii=False, use_decimal=True)
            
            print(f"成功转换: {os.path.basename(input_file)} -> {os.path.basename(output_json)}")
        
        except Exception as e:
            # 记录错误信息和完整文件路径到列表
            error_records.append({
                'file_path': input_file,
                'error_message': str(e)
            })
    
    # 最后统一打印错误信息
    if error_records:
        print(f"\n=== 错误汇总 ===")
        print(f"共遇到 {len(error_records)} 个错误:")
        for i, record in enumerate(error_records, 1):
            print(f"{i}. 文件: {record['file_path']}")
            print(f"   错误: {record['error_message']}\n")
    else:
        print(f"\n所有文件转换完成，无错误发生！")


if __name__ == "__main__":
    batch_convert_decompressed_files(r"Y:\model", 'decompressed')
    
    # input_file = r"Y:\model\effect\1043.scsp.decompressed"
    # # # # # if not os.path.exists(input_file):
    # # # # #     print(f"Error: {input_file} not found.")
    # # # # #     sys.exit(1)
    # reader =  BinaryReader(input_file)
    # parser = SpineSkeletonParser(reader)
    # result = parser.parse()
    
    # # 将 numpy 类型转换为 Python 原生类型，以便 JSON 序列化
    # def convert_numpy_types(obj):
    #         import numpy as np
    #         if isinstance(obj, np.integer):
    #             return int(obj)
    #         elif isinstance(obj, np.floating):
    #             return float(obj)
    #         elif isinstance(obj, np.ndarray):
    #             return obj.tolist()  # 转换为 Python 列表
    #         elif isinstance(obj, list):
    #             return [convert_numpy_types(item) for item in obj]
    #         elif isinstance(obj, dict):
    #             return {key: convert_numpy_types(value) for key, value in obj.items()}
    #         else:
    #             return obj

    # result = convert_numpy_types(result)
    
    # with open(r"Y:\model\liveevent_1056.json", 'w', encoding='utf-8') as f:
    #     json.dump(result, f, indent=4, ensure_ascii=False, use_decimal=True)
    

