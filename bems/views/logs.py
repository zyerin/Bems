from django.shortcuts import render
import os

def view_logs(request):
    try:
        log_dir = os.path.join(os.path.dirname(__file__), '..', 'Logs')
        log_file = os.path.join(log_dir, "log.txt")

        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                log_lines = f.readlines()
        else:
            log_lines = ["[Log 파일이 존재하지 않습니다.]"]

    except Exception as e:
        log_lines = [f"[로그 파일을 읽는 중 오류 발생: {str(e)}]"]

    return render(request, 'bems/logs.html', {'log_lines': log_lines})
