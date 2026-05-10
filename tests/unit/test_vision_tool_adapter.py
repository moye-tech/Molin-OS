#!/usr/bin/env python3
"""
视觉分析工具适配器单元测试

测试 VisionToolAdapter 类的功能，包括图像分析、对象检测、人脸识别等
"""

import sys
import os
import unittest
import json
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from hermes_fusion.integration.external_tools.vision_tools import VisionToolAdapter


class TestVisionToolAdapter(unittest.TestCase):
    """视觉分析工具适配器测试类"""

    def setUp(self):
        """设置测试环境"""
        self.adapter = VisionToolAdapter()

    def test_adapter_initialization(self):
        """测试适配器初始化"""
        self.assertEqual(self.adapter.tool_name, "vision_analyze_image")
        self.assertEqual(self.adapter.external_module, "deep_live_cam.core")
        self.assertEqual(self.adapter.external_function, "analyze")
        self.assertEqual(self.adapter.toolset, "vision")

    def test_analyze_image_general(self):
        """测试通用图像分析"""
        # 测试base64图像数据
        mock_image_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        result = self.adapter.analyze_image(mock_image_data, analysis_type="general")

        # 验证结果结构
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["source"], "mock")
        self.assertEqual(result["result"]["analysis_type"], "general")
        self.assertIn("image_info", result["result"])
        self.assertIn("analysis", result["result"])
        self.assertIn("recommendations", result["result"])

        # 验证分析结果
        analysis = result["result"]["analysis"]
        self.assertIn("image_size", analysis)
        self.assertIn("estimated_resolution", analysis)
        self.assertIn("color_profile", analysis)
        self.assertIn("detected_objects", analysis)

    def test_analyze_image_face(self):
        """测试人脸图像分析"""
        mock_image_data = "data:image/png;base64,mock_face_image"

        result = self.adapter.analyze_image(mock_image_data, analysis_type="face")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"]["analysis_type"], "face")

        analysis = result["result"]["analysis"]
        self.assertIn("face_count", analysis)
        self.assertIn("faces", analysis)
        self.assertIn("dominant_emotion", analysis)

        # 验证人脸数据
        faces = analysis["faces"]
        self.assertEqual(len(faces), 2)  # 模拟返回2个人脸

        # 验证每个人脸的属性
        for face in faces:
            self.assertIn("bounding_box", face)
            self.assertIn("confidence", face)
            self.assertIn("age", face)
            self.assertIn("gender", face)
            self.assertIn("emotion", face)
            self.assertEqual(len(face["bounding_box"]), 4)  # [x1, y1, x2, y2]

    def test_analyze_image_object(self):
        """测试对象检测图像分析"""
        mock_image_data = b"mock_binary_image_data"

        result = self.adapter.analyze_image(mock_image_data, analysis_type="object")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"]["analysis_type"], "object")

        analysis = result["result"]["analysis"]
        self.assertIn("object_count", analysis)
        self.assertIn("objects", analysis)
        self.assertIn("scene_context", analysis)

        # 验证对象数据
        objects = analysis["objects"]
        self.assertEqual(len(objects), 3)  # 模拟返回3个对象

        for obj in objects:
            self.assertIn("class", obj)
            self.assertIn("confidence", obj)
            self.assertIn("bbox", obj)
            self.assertEqual(len(obj["bbox"]), 4)

    def test_detect_objects(self):
        """测试对象检测"""
        mock_image_data = "mock_image_base64"
        object_classes = ["person", "car", "chair"]

        result = self.adapter.detect_objects(
            mock_image_data,
            object_classes=object_classes,
            confidence_threshold=0.6
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["source"], "mock")

        result_data = result["result"]
        self.assertIn("detected_objects", result_data)
        self.assertIn("total_objects", result_data)
        self.assertEqual(result_data["confidence_threshold"], 0.6)
        self.assertEqual(result_data["object_classes_requested"], object_classes)
        self.assertIn("object_classes_detected", result_data)
        self.assertIn("analysis_details", result_data)

        # 验证检测到的对象
        detected_objects = result_data["detected_objects"]
        self.assertGreater(len(detected_objects), 0)

        for obj in detected_objects:
            self.assertIn("class", obj)
            self.assertIn("confidence", obj)
            self.assertIn("bounding_box", obj)
            self.assertIn("area", obj)
            # 置信度应大于等于阈值
            self.assertGreaterEqual(obj["confidence"], 0.6)

    def test_recognize_faces_without_features(self):
        """测试人脸识别（不提取特征）"""
        mock_image_data = b"binary_image_data"

        result = self.adapter.recognize_faces(
            mock_image_data,
            extract_features=False,
            match_faces=False,
            face_database=None
        )

        self.assertEqual(result["status"], "success")

        result_data = result["result"]
        self.assertIn("faces_detected", result_data)
        self.assertIn("faces", result_data)
        self.assertIn("extract_features", result_data)
        self.assertIn("match_faces", result_data)
        self.assertIn("database_size", result_data)
        self.assertIn("analysis_summary", result_data)

        # 验证人脸数据
        faces = result_data["faces"]
        self.assertEqual(len(faces), 2)  # 模拟返回2个人脸

        for face in faces:
            self.assertIn("face_id", face)
            self.assertIn("bounding_box", face)
            self.assertIn("confidence", face)
            self.assertIn("landmarks", face)
            self.assertIn("attributes", face)

            # 验证特征点
            landmarks = face["landmarks"]
            expected_landmarks = ["left_eye", "right_eye", "nose", "mouth_left", "mouth_right"]
            for landmark in expected_landmarks:
                self.assertIn(landmark, landmarks)
                self.assertEqual(len(landmarks[landmark]), 2)  # [x, y]

            # 验证属性
            attributes = face["attributes"]
            expected_attrs = ["age", "gender", "emotion", "glasses", "mask"]
            for attr in expected_attrs:
                self.assertIn(attr, attributes)

        # 验证没有特征提取
        for face in faces:
            self.assertNotIn("features", face)

    def test_recognize_faces_with_features(self):
        """测试人脸识别（提取特征）"""
        mock_image_data = "base64_image_data"

        result = self.adapter.recognize_faces(
            mock_image_data,
            extract_features=True,
            match_faces=False,
            face_database=None
        )

        self.assertEqual(result["status"], "success")

        result_data = result["result"]
        faces = result_data["faces"]

        # 验证特征提取
        for face in faces:
            self.assertIn("features", face)
            features = face["features"]
            self.assertIn("embedding", features)
            self.assertIn("feature_version", features)

            # 验证嵌入向量维度
            embedding = features["embedding"]
            self.assertIsInstance(embedding, list)
            self.assertEqual(len(embedding), 128)  # 模拟返回128维向量

    def test_recognize_faces_with_matching(self):
        """测试人脸识别（带匹配功能）"""
        mock_image_data = "base64_image_data"
        face_database = [
            {"id": "db_person_001", "name": "张三", "features": [0.1] * 128},
            {"id": "db_person_002", "name": "李四", "features": [0.2] * 128}
        ]

        result = self.adapter.recognize_faces(
            mock_image_data,
            extract_features=True,
            match_faces=True,
            face_database=face_database
        )

        self.assertEqual(result["status"], "success")

        result_data = result["result"]
        self.assertIn("matches", result_data)
        self.assertEqual(result_data["database_size"], len(face_database))

        # 验证匹配结果
        matches = result_data["matches"]
        self.assertGreater(len(matches), 0)

        for match in matches:
            self.assertIn("face_id", match)
            self.assertIn("matched_id", match)
            self.assertIn("similarity_score", match)
            self.assertIn("is_match", match)

    def test_analyze_video_stream(self):
        """测试视频流分析"""
        video_source = "test_video.mp4"
        analysis_types = ["motion", "face", "object"]
        duration_seconds = 10

        result = self.adapter.analyze_video_stream(
            video_source,
            analysis_types=analysis_types,
            duration_seconds=duration_seconds,
            callback_url="https://example.com/callback"
        )

        self.assertEqual(result["status"], "success")

        result_data = result["result"]
        self.assertEqual(result_data["video_source"], video_source)
        self.assertEqual(result_data["analysis_types"], analysis_types)
        self.assertEqual(result_data["duration_seconds"], duration_seconds)
        self.assertIn("frames_analyzed", result_data)
        self.assertIn("events_detected", result_data)
        self.assertIn("events", result_data)
        self.assertIn("analysis_summary", result_data)
        self.assertEqual(result_data["callback_status"], "notified")

        # 验证事件数据
        events = result_data["events"]
        self.assertGreater(len(events), 0)

        for event in events:
            self.assertIn("timestamp", event)
            self.assertIn("event_type", event)
            self.assertIn("confidence", event)
            self.assertIn("location", event)
            self.assertIn("description", event)

            # 位置应该是边界框
            location = event["location"]
            self.assertEqual(len(location), 4)  # [x1, y1, x2, y2]

        # 验证分析摘要
        summary = result_data["analysis_summary"]
        self.assertIn("start_time", summary)
        self.assertIn("end_time", summary)
        self.assertIn("processing_fps", summary)
        self.assertIn("total_processing_time_ms", summary)

    def test_swap_faces(self):
        """测试人脸交换"""
        source_image = "data:image/png;base64,source_mock"
        target_image = b"target_binary_image"
        parameters = {
            "blend_strength": 0.8,
            "preserve_lighting": True,
            "smooth_edges": True
        }

        result = self.adapter.swap_faces(source_image, target_image, parameters)

        self.assertEqual(result["status"], "success")

        result_data = result["result"]
        self.assertEqual(result_data["source_faces"], 1)
        self.assertEqual(result_data["target_faces"], 1)
        self.assertEqual(result_data["faces_swapped"], 1)
        self.assertEqual(result_data["parameters"], parameters)
        self.assertIn("result_image", result_data)
        self.assertIn("processing_details", result_data)

        # 验证处理详情
        processing_details = result_data["processing_details"]
        self.assertIn("processing_time_ms", processing_details)
        self.assertIn("algorithm", processing_details)
        self.assertIn("model", processing_details)
        self.assertIn("quality_score", processing_details)

        # 验证结果图像
        result_image = result_data["result_image"]
        self.assertTrue(result_image.startswith("data:image/png;base64,"))

    def test_swap_faces_default_parameters(self):
        """测试人脸交换使用默认参数"""
        source_image = "mock_source"
        target_image = "mock_target"

        result = self.adapter.swap_faces(source_image, target_image)

        self.assertEqual(result["status"], "success")

        result_data = result["result"]
        self.assertIn("parameters", result_data)

        # 验证默认参数
        parameters = result_data["parameters"]
        expected_defaults = {
            "blend_strength": 0.8,
            "preserve_lighting": True,
            "smooth_edges": True
        }

        for key, value in expected_defaults.items():
            self.assertEqual(parameters[key], value)

    def test_adapter_with_mock_external_module(self):
        """测试适配器使用模拟外部模块的情况"""
        # 在模拟模式下测试（当Deep-Live-Cam不可用时）
        # VisionToolAdapter 会自动使用模拟方法

        # 测试所有主要方法
        test_cases = [
            ("analyze_image", ("mock_image", "general", None)),
            ("detect_objects", ("mock_image", ["person", "car"], 0.5)),
            ("recognize_faces", ("mock_image", False, False, None)),
            ("analyze_video_stream", ("test.mp4", ["motion"], 30, None)),
            ("swap_faces", ("source", "target", None)),
        ]

        for method_name, args in test_cases:
            method = getattr(self.adapter, method_name)

            try:
                result = method(*args)
                self.assertEqual(result["status"], "success")
                self.assertEqual(result["source"], "mock")
            except Exception as e:
                self.fail(f"方法 {method_name} 失败: {e}")

    def test_check_deep_live_cam_availability(self):
        """测试Deep-Live-Cam可用性检查"""
        # 由于我们还没有安装Deep-Live-Cam，应该返回False
        availability = self.adapter.deep_live_cam_available

        # 可以是False或True，取决于环境
        self.assertIsInstance(availability, bool)

        # 如果返回False，确保模拟方法正常工作
        if not availability:
            result = self.adapter.analyze_image("mock", "general")
            self.assertEqual(result["source"], "mock")

    def test_error_handling(self):
        """测试错误处理"""
        # 测试无效输入类型
        with self.assertRaises(Exception):
            # 传入无效的图像数据类型
            self.adapter.analyze_image(123, "general")  # 整数不是有效图像数据

        # 测试无效分析类型
        result = self.adapter.analyze_image("mock", "invalid_type")
        # 应该回退到通用分析
        self.assertEqual(result["result"]["analysis_type"], "invalid_type")
        # 但结构应该仍然是完整的
        self.assertEqual(result["status"], "success")


if __name__ == "__main__":
    unittest.main()