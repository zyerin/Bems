from django.shortcuts import render
from ..models import Manager, Engineer

# 기본 메인(테스트) 페이지
def main_view(request):
    return render(request, 'bems/index.html')


# 전화번호부를 화면에 출력하는 뷰
def phonebook_view(request):
    # 모든 Manager, Engineer 객체(항목) 가져옴
    managers = Manager.objects.all()
    engineers = Engineer.objects.all()

    # 템플릿에 전달할 데이터 context 구성
    context = {
        'managers': managers,
        'engineers': engineers

    }

    return render(request, 'bems/phonebook.html', context) # 템플릿 렌더링