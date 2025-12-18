"""
基础API测试脚本
用于验证API功能是否正常
"""
import requests
import json

# API基础URL
BASE_URL = "http://localhost:8000"


def test_health_check():
    """测试健康检查"""
    print("\n1. 测试健康检查...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")
    assert response.status_code == 200


def test_user_login():
    """测试用户登录"""
    print("\n2. 测试用户登录...")
    data = {"phone": "13800138000"}
    response = requests.post(f"{BASE_URL}/api/users/login", json=data)
    print(f"   状态码: {response.status_code}")
    result = response.json()
    print(f"   用户ID: {result.get('id')}")
    print(f"   手机号: {result.get('phone')}")
    assert response.status_code == 200
    return result


def test_get_batches():
    """测试获取批次列表"""
    print("\n3. 测试获取批次列表...")
    response = requests.get(f"{BASE_URL}/api/batches")
    print(f"   状态码: {response.status_code}")
    result = response.json()
    print(f"   批次总数: {result.get('total')}")
    if result.get('batches'):
        batch = result['batches'][0]
        print(f"   第一个批次: {batch.get('essay_title')[:30]}...")
        return batch.get('id')
    assert response.status_code == 200


def test_get_essays(batch_id=None):
    """测试获取作文列表"""
    print("\n4. 测试获取作文列表...")
    params = {"page": 1, "page_size": 5}
    if batch_id:
        params["batch_id"] = batch_id

    response = requests.get(f"{BASE_URL}/api/essays", params=params)
    print(f"   状态码: {response.status_code}")
    result = response.json()
    print(f"   作文总数: {result.get('total')}")
    print(f"   当前页: {result.get('page')}/{result.get('total_pages')}")

    if result.get('essays'):
        essay = result['essays'][0]
        print(f"   第一篇作文:")
        print(f"     - 学生: {essay.get('student_name')}")
        print(f"     - 字数: {essay.get('word_count')}")
        print(f"     - 分制: {essay.get('score_system')}分制")
        return essay.get('id')
    assert response.status_code == 200


def test_get_essay_detail(essay_id):
    """测试获取作文详情"""
    print(f"\n5. 测试获取作文详情 (ID: {essay_id})...")
    response = requests.get(f"{BASE_URL}/api/essays/{essay_id}")
    print(f"   状态码: {response.status_code}")
    result = response.json()
    print(f"   题目: {result.get('batch', {}).get('essay_title', '')[:40]}...")
    print(f"   字数: {result.get('word_count')}")
    print(f"   分制: {result.get('score_system')}分制")
    assert response.status_code == 200
    return result


def main():
    """主测试流程"""
    print("=" * 60)
    print("作文评分系统 - API基础测试")
    print("=" * 60)

    try:
        # 1. 健康检查
        test_health_check()

        # 2. 用户登录
        user = test_user_login()

        # 3. 获取批次列表
        batch_id = test_get_batches()

        # 4. 获取作文列表
        essay_id = test_get_essays(batch_id)

        # 5. 获取作文详情
        if essay_id:
            essay_detail = test_get_essay_detail(essay_id)

        print("\n" + "=" * 60)
        print("✅ 所有基础测试通过!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
