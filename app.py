from flask import Flask, render_template, request, jsonify
import requests
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import sqlite3
import hashlib

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv('NINEHIRE_API_KEY')
BASE_URL = 'https://api.ninehire.com/api/v1'

# 데이터베이스 초기화
def init_db():
    try:
        # 기존 데이터베이스 파일이 있으면 삭제
        if os.path.exists('settings.db'):
            os.remove('settings.db')
            
        conn = sqlite3.connect('settings.db')
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                manager_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                selected_questions TEXT NOT NULL,
                custom_questions TEXT NOT NULL,
                custom_columns TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        print("데이터베이스가 성공적으로 초기화되었습니다.")
    except Exception as e:
        print(f"데이터베이스 초기화 중 오류 발생: {str(e)}")
        raise
    finally:
        conn.close()

# 앱 시작 시 데이터베이스 초기화
init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/applicants')
def get_applicants():
    job_id = request.args.get('jobId')
    if not job_id:
        return jsonify({'error': 'Job ID is required'}), 400

    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    params = {
        'jobId': job_id,
        'include': 'resume,answers,education,experience,license,language,military,veteran,disability',
        'status': 'all',
        'page': 1,
        'per_page': 100,
        'fields': 'id,name,email,phoneNumber,appliedAt,updatedAt,status,source,recruitment,step,customAnswers,educations,experiences,licenses,languages,militaryService,veteranStatus,disability,gender,birthday'
    }

    all_results = []
    page = 1
    has_more = True
    last_response_length = 0

    while has_more:
        params['page'] = page
        response = requests.get(
            f'{BASE_URL}/applicants',
            headers=headers,
            params=params
        )

        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch applicants'}), 500

        data = response.json()
        
        if data.get('results'):
            all_results.extend(data['results'])
            
            if len(data['results']) == 0 or len(data['results']) == last_response_length:
                has_more = False
            else:
                last_response_length = len(data['results'])
                page += 1
        else:
            has_more = False

    return jsonify({'results': all_results})

@app.route('/api/save-settings', methods=['POST'])
def save_settings():
    data = request.json
    
    # 필수 필드 확인
    required_fields = ['jobId', 'managerName', 'password', 'selectedQuestions', 'customQuestions', 'customColumns']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        conn = sqlite3.connect('settings.db')
        c = conn.cursor()
        
        # 비밀번호 해시화
        password_hash = hash_password(data['password'])
        
        # 설정 ID가 있으면 업데이트, 없으면 새로 생성
        if 'id' in data:
            # 기존 설정 확인
            c.execute('SELECT password_hash FROM settings WHERE id = ?', (data['id'],))
            row = c.fetchone()
            if not row:
                return jsonify({'error': 'Settings not found'}), 404
            
            # 비밀번호 확인
            if hash_password(data['password']) != row[0]:
                return jsonify({'error': 'Invalid password'}), 401
            
            # 설정 업데이트
            c.execute('''
                UPDATE settings 
                SET job_id = ?, manager_name = ?, password_hash = ?, 
                    selected_questions = ?, custom_questions = ?, custom_columns = ?
                WHERE id = ?
            ''', (
                data['jobId'],
                data['managerName'],
                password_hash,
                json.dumps(data['selectedQuestions']),
                json.dumps(data['customQuestions']),
                json.dumps(data['customColumns']),
                data['id']
            ))
            setting_id = data['id']
        else:
            # 새 설정 저장
            c.execute('''
                INSERT INTO settings (job_id, manager_name, password_hash, selected_questions, custom_questions, custom_columns)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                data['jobId'],
                data['managerName'],
                password_hash,
                json.dumps(data['selectedQuestions']),
                json.dumps(data['customQuestions']),
                json.dumps(data['customColumns'])
            ))
            setting_id = c.lastrowid
        
        conn.commit()
        return jsonify({'message': 'Settings saved successfully', 'id': setting_id}), 200
    except Exception as e:
        print(f"설정 저장 중 오류 발생: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/saved-settings', methods=['GET'])
def get_saved_settings():
    try:
        conn = sqlite3.connect('settings.db')
        c = conn.cursor()
        
        c.execute('''
            SELECT id, job_id, manager_name, created_at
            FROM settings
            ORDER BY created_at DESC
        ''')
        
        settings = [
            {
                'id': row[0],
                'jobId': row[1],
                'managerName': row[2],
                'createdAt': row[3]
            }
            for row in c.fetchall()
        ]
        
        return jsonify(settings), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/load-settings/<int:setting_id>', methods=['POST'])
def load_settings(setting_id):
    data = request.json
    if 'password' not in data:
        return jsonify({'error': 'Password is required'}), 400
    
    try:
        conn = sqlite3.connect('settings.db')
        c = conn.cursor()
        
        # 설정 조회
        c.execute('''
            SELECT job_id, manager_name, password_hash, selected_questions, custom_questions, custom_columns
            FROM settings
            WHERE id = ?
        ''', (setting_id,))
        
        row = c.fetchone()
        if not row:
            return jsonify({'error': 'Settings not found'}), 404
        
        # 비밀번호 확인
        if hash_password(data['password']) != row[2]:
            return jsonify({'error': 'Invalid password'}), 401
        
        # 설정 반환
        return jsonify({
            'jobId': row[0],
            'managerName': row[1],
            'selectedQuestions': json.loads(row[3]),
            'customQuestions': json.loads(row[4]),
            'customColumns': json.loads(row[5])
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/delete-settings/<int:setting_id>', methods=['DELETE'])
def delete_settings(setting_id):
    data = request.json
    if 'password' not in data:
        return jsonify({'error': 'Password is required'}), 400
    
    try:
        conn = sqlite3.connect('settings.db')
        c = conn.cursor()
        
        # 비밀번호 확인
        c.execute('SELECT password_hash FROM settings WHERE id = ?', (setting_id,))
        row = c.fetchone()
        if not row:
            return jsonify({'error': 'Settings not found'}), 404
        
        if hash_password(data['password']) != row[0]:
            return jsonify({'error': 'Invalid password'}), 401
        
        # 설정 삭제
        c.execute('DELETE FROM settings WHERE id = ?', (setting_id,))
        conn.commit()
        
        return jsonify({'message': 'Settings deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True) 