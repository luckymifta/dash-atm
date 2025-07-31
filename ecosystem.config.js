module.exports = {
  apps: [
    {
      name: 'atm-backend-main',
      script: 'venv/bin/python',
      args: '-m uvicorn main:app --host 0.0.0.0 --port 8000',
      cwd: '/home/luckymifta/dash-atm',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '/home/luckymifta/dash-atm'
      },
      env_production: {
        NODE_ENV: 'production',
        PYTHONPATH: '/home/luckymifta/dash-atm'
      },
      error_file: './logs/backend-main-error.log',
      out_file: './logs/backend-main-out.log',
      log_file: './logs/backend-main-combined.log',
      time: true,
      log_date_format: 'YYYY-MM-DD HH:mm Z',
      merge_logs: true,
      kill_timeout: 5000,
      listen_timeout: 8000,
      reload_delay: 1000
    },
    {
      name: 'atm-backend-user',
      script: 'venv/bin/python',
      args: '-m uvicorn user_management.main:app --host 0.0.0.0 --port 8001',
      cwd: '/home/luckymifta/dash-atm',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '/home/luckymifta/dash-atm'
      },
      env_production: {
        NODE_ENV: 'production',
        PYTHONPATH: '/home/luckymifta/dash-atm'
      },
      error_file: './logs/backend-user-error.log',
      out_file: './logs/backend-user-out.log',
      log_file: './logs/backend-user-combined.log',
      time: true,
      log_date_format: 'YYYY-MM-DD HH:mm Z',
      merge_logs: true,
      kill_timeout: 5000,
      listen_timeout: 8000,
      reload_delay: 1000
    },
    {
      name: 'atm-frontend',
      script: 'npm',
      args: 'start',
      cwd: '/home/luckymifta/dash-atm/frontend',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PORT: 3000
      },
      env_production: {
        NODE_ENV: 'production',
        PORT: 3000
      },
      error_file: '../logs/frontend-error.log',
      out_file: '../logs/frontend-out.log',
      log_file: '../logs/frontend-combined.log',
      time: true,
      log_date_format: 'YYYY-MM-DD HH:mm Z',
      merge_logs: true,
      kill_timeout: 5000,
      listen_timeout: 8000,
      reload_delay: 1000
    }
  ],

  deploy: {
    production: {
      user: 'luckymifta',
      host: 'dash.britimorleste.tl',
      ref: 'origin/main',
      repo: 'https://github.com/luckymifta/dash-atm.git',
      path: '/home/luckymifta/dash-atm',
      'pre-deploy-local': '',
      'post-deploy': 'source venv/bin/activate && pip install -r requirements.txt && cd frontend && npm install && npm run build && pm2 reload ecosystem.config.js --env production',
      'pre-setup': ''
    }
  }
};
