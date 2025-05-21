from django.shortcuts import render
from ..models import Manager

# 기본 메인(테스트) 페이지
def main_view(request):
    return render(request, 'bems/index.html')


# 전화번호부를 화면에 출력하는 뷰
def phonebook_view(request):
    # 모든 Manager 항목을 가져옴
    phonebook_entries = Manager.objects.all()

    # 템플릿에 전달할 데이터 context 구성
    context = {
        'phonebook_entries': phonebook_entries,
    }

    return render(request, 'bems/phonebook.html', context) # 템플릿 렌더링