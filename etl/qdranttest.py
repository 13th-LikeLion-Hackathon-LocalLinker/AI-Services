"""
Qdrant 연결 테스트
"""

from qdrant_client import QdrantClient


def check_collections():
    client = QdrantClient(host="localhost", port=6333)

    try:
        collections = client.get_collections()

        if not collections.collections:
            print("생성된 컬렉션이 없습니다.")
            return

        print(f"✅ 총 {len(collections.collections)}개 컬렉션 발견")
        print()

        for collection in collections.collections:
            print(f"📁 {collection.name}")

            # 상세 정보 조회
            try:
                info = client.get_collection(collection.name)

                print(f"   상태: {info.status}")
                print(f"   포인트 수: {info.points_count:,}")
                print(f"   세그먼트 수: {info.segments_count}")
                print(f"   벡터 크기: {info.config.params.vectors.size}")
                print(f"   거리 측정: {info.config.params.vectors.distance}")
                print(f"   최적화 상태: {info.optimizer_status}")

                # 경고 메시지 제거
                if info.vectors_count is None:
                    print(f"   벡터 수: {info.points_count:,} (vectors_count는 deprecated)")
                else:
                    print(f"   벡터 수: {info.vectors_count:,}")

            except Exception as e:
                print(f"   ❌ 상세 정보 조회 실패: {e}")
            print()

    except Exception as e:
        print(f"Qdrant 연결 실패: {e}")


if __name__ == "__main__":
    check_collections()