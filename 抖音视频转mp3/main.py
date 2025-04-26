import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, 
                            QFileDialog, QLabel, QVBoxLayout, QHBoxLayout,
                            QWidget, QSlider, QTimeEdit, QMessageBox, QProgressBar,QLineEdit)
from PyQt5.QtCore import Qt, QTime, QUrl, QSettings, QTimer
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from moviepy.editor import VideoFileClip
from datetime import datetime
from PyQt5.QtGui import QDesktopServices

class DouYinConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.video_path = None
        self.output_path = None
        self.video_duration = 0
        
        # 加载上次保存的输出文件夹路径
        self.settings = QSettings("DouYinConverter", "Settings")
        last_output_path = self.settings.value("last_output_path", "")
        if last_output_path and os.path.exists(last_output_path):
            self.output_path = last_output_path
            self.output_label.setText("输出文件夹:")
            self.output_btn.setText(os.path.basename(last_output_path))
        
    def initUI(self):
        # 设置窗口
        self.setWindowTitle('抖音视频转MP3工具')
        # 获取屏幕尺寸并居中显示窗口
        screen = QApplication.desktop().screenGeometry()
        width, height = 400, 800
        left = (screen.width() - width) // 2-200
        top = (screen.height() - height) // 2-100
        self.setGeometry(left, top, width, height)
        
        # 创建主布局
        main_layout = QVBoxLayout()
        
        # 文件选择部分
        file_layout = QHBoxLayout()
        self.file_label = QLabel('未选择文件')
        self.file_btn = QPushButton('选择视频文件')
        self.file_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.file_btn)
        main_layout.addLayout(file_layout)
        
        # 视频信息显示
        self.info_label = QLabel('视频信息: 无')
        main_layout.addWidget(self.info_label)
        
        # 视频预览部分
        preview_layout = QVBoxLayout()
        preview_label = QLabel('视频预览:')
        preview_layout.addWidget(preview_label)
        
        # 添加视频播放器
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(600)
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.error.connect(self.handle_media_error)
        preview_layout.addWidget(self.video_widget)
        
        # 添加播放控制
        controls_layout = QHBoxLayout()
        
        # 播放/暂停按钮
        self.play_btn = QPushButton('播放')
        self.play_btn.clicked.connect(self.toggle_play)
        self.play_btn.setEnabled(False)
        controls_layout.addWidget(self.play_btn)
        
        # 进度条
        self.video_slider = QSlider(Qt.Horizontal)
        self.video_slider.setRange(0, 0)
        self.video_slider.sliderMoved.connect(self.set_position)
        self.video_slider.mousePressEvent = self.slider_clicked
        controls_layout.addWidget(self.video_slider)
        
        # 时间标签
        self.time_label = QLabel('00:00:00 / 00:00:00')
        controls_layout.addWidget(self.time_label)
        
        preview_layout.addLayout(controls_layout)
        main_layout.addLayout(preview_layout)
        
        # 时间选择部分
        time_layout = QHBoxLayout()
        time_label = QLabel('选择音频截取时间段:  ')
        time_layout.addWidget(time_label)
        
        # 开始时间
        start_label = QLabel('开始时间:')
        self.start_time = QTimeEdit()
        self.start_time.setDisplayFormat("mm:ss.zzz")
        self.start_time.setTime(QTime(0, 0, 0))
        time_layout.addWidget(start_label)
        time_layout.addWidget(self.start_time)

        # 结束时间
        end_label = QLabel('结束时间:')
        self.end_time = QTimeEdit()
        self.end_time.setDisplayFormat("mm:ss.zzz")
        self.end_time.setTime(QTime(0, 0, 0))
        time_layout.addWidget(end_label)
        time_layout.addWidget(self.end_time)

        time_layout.addStretch()
        
        main_layout.addLayout(time_layout)
        
        #文件名设置
        file_layout = QHBoxLayout()
        self.file_name_label = QLabel('文件名:')
        self.file_name_edit = QLineEdit()
        self.file_name_edit.setText('抖音收藏'+datetime.now().strftime('%m%d_%H%M%S'))
        self.file_name_edit.setFixedWidth(200)
        file_layout.addWidget(self.file_name_label)
        file_layout.addWidget(self.file_name_edit)
        file_layout.addStretch()

        # 输出文件选择
        self.output_label = QLabel('未设置输出文件夹')
        self.output_btn = QPushButton('选择输出文件夹')
        self.output_btn.clicked.connect(self.select_output_folder)
        file_layout.addWidget(self.output_label)
        file_layout.addWidget(self.output_btn)


        main_layout.addLayout(file_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
        
        # 转换按钮
        self.convert_btn = QPushButton('开始转换')
        self.convert_btn.clicked.connect(self.convert_video)
        self.convert_btn.setEnabled(False)
        main_layout.addWidget(self.convert_btn)
        
        # 设置主窗口布局
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
    def select_file(self):
        # 获取上次加载的文件夹路径
        recent_load_file = self.settings.value("recent_load_file", "")
        if recent_load_file:
            file_path, _ = QFileDialog.getOpenFileName(
                self, '选择抖音视频', recent_load_file, '视频文件 (*.mp4 *.mkv *.avi)'
            )
        else:
            file_path, _ = QFileDialog.getOpenFileName(
                self, '选择抖音视频', '', '视频文件 (*.mp4 *.mkv *.avi)'
            )
        if file_path:
            self.video_path = file_path
            self.file_label.setText(os.path.basename(file_path))
            self.settings.setValue("recent_load_file", file_path[:file_path.rfind('/')+1])
            # 获取视频信息
            try:

                clip = VideoFileClip(file_path)
                self.video_duration = clip.duration
                
                adjusted_duration = max(0, self.video_duration)
                
                minutes, seconds = divmod(int(adjusted_duration), 60)
                milliseconds = int((adjusted_duration - int(adjusted_duration)) * 1000)
                self.end_time.setTime(QTime(0, minutes, seconds-3, milliseconds))

                # 显示视频信息
                total_minutes = int(self.video_duration // 60)
                seconds = int(self.video_duration % 60)
                milliseconds = int((self.video_duration - int(self.video_duration)) * 1000)
                self.info_label.setText(f'视频信息: 时长 {total_minutes:02d}:{seconds:02d}.{milliseconds:03d}, 大小: {os.path.getsize(file_path) / (1024*1024):.2f} MB')
                
                clip.close()
                
                # 加载视频到播放器
                self.load_video(file_path)
                
                # 如果已经选择了输出文件，激活转换按钮
                if self.output_path:
                    self.convert_btn.setEnabled(True)
                    
            except Exception as e:
                QMessageBox.warning(self, '错误', f'无法读取视频文件: {str(e)}')
    
    def load_video(self, file_path):
        # 设置媒体播放器的内容
        try:
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
            # 播放一瞬间然后暂停以显示第一帧
            self.media_player.play()
            # 使用短暂延迟后暂停
            QTimer.singleShot(5, self.media_player.pause)
            self.play_btn.setEnabled(True)
            self.play_btn.setText('播放')
        except Exception as e:
            print(f"加载视频出错: {str(e)}")
            # 即使视频预览失败，我们也允许音频转换继续
            if self.output_path:
                self.convert_btn.setEnabled(True)
    
    def handle_media_error(self, error):
        error_msg = self.media_player.errorString()
        print(f"媒体播放器错误: {error} - {error_msg}")
        
        # 创建包含下载按钮的消息框
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('预览警告')
        msg_box.setText('视频预览功能不可用，可能是由于缺少编解码器或不支持的格式。\n'
                         '这不会影响音频转换功能，您仍然可以继续转换。')
        
        # 添加按钮
        download_button = msg_box.addButton('下载解码器', QMessageBox.ActionRole)
        msg_box.addButton('关闭', QMessageBox.RejectRole)
        
        msg_box.exec_()
        
        # 根据用户选择的按钮执行相应操作
        if msg_box.clickedButton() == download_button:
            self.open_codec_download_page()
    
    def open_codec_download_page(self):
        """打开解码器下载页面"""
        codec_url = QUrl("https://files2.codecguide.com/K-Lite_Codec_Pack_1890_Standard.exe")
        QDesktopServices.openUrl(codec_url)
    
    def toggle_play(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_btn.setText('播放')
        else:
            self.media_player.play()
            self.play_btn.setText('暂停')
    
    def position_changed(self, position):
        # 更新滑块位置
        self.video_slider.setValue(position)
        
        # 更新时间标签
        current_time = QTime(0, 0, 0).addMSecs(position)
        total_time = QTime(0, 0, 0).addMSecs(self.media_player.duration())
        self.time_label.setText(f'{current_time.toString("mm:ss.zzz")} / {total_time.toString("mm:ss.zzz")}')
        

    
    def duration_changed(self, duration):
        # 设置滑块范围
        self.video_slider.setRange(0, duration)
    
    def set_position(self, position):
        # 设置播放位置
        self.media_player.setPosition(position)
        
    def slider_clicked(self, event):
        # 处理滑块上的点击事件
        if self.media_player.duration() > 0:
            # 计算点击位置相对于滑块宽度的比例
            click_position = event.pos().x()
            slider_width = self.video_slider.width()
            # 计算相应的视频位置
            relative_position = click_position / slider_width
            position = int(relative_position * self.media_player.duration())
            # 设置滑块位置和视频位置
            self.video_slider.setValue(position)
            self.media_player.setPosition(position)
    
    def select_output_folder(self):
        file_path= QFileDialog.getExistingDirectory(
            self, '选择输出文件夹'
        )
        
        if file_path:
            # 如果文件夹不存在，则创建
            if not os.path.exists(file_path):
                os.makedirs(file_path)
                
            self.output_path = file_path
            self.output_label.setText("输出文件夹:")
            self.output_btn.setText(os.path.basename(file_path))
            
            # 保存选择的输出文件夹路径
            self.settings.setValue("last_output_path", file_path)
            
            # 如果已经选择了输入文件，激活转换按钮
            if self.video_path:
                self.convert_btn.setEnabled(True)
    
    def convert_video(self):
        if not self.video_path or not self.output_path:
            return
        
        # 获取开始和结束时间（以秒为单位）
        start_time = self.time_to_mseconds(self.start_time.time())
        end_time = self.time_to_mseconds(self.end_time.time())
        
        # 验证时间是否有效
        if start_time >= end_time:
            QMessageBox.warning(self, '错误', '开始时间必须小于结束时间')
            return
        
        if end_time > self.video_duration:
            QMessageBox.warning(self, '错误', '结束时间不能超过视频时长')
            return
        
        try:
            # 禁用按钮，防止重复点击
            self.convert_btn.setEnabled(False)
            self.progress_bar.setValue(10)
            
            # 进行转换
            video = VideoFileClip(self.video_path)
            self.progress_bar.setValue(30)
            
            # 裁剪视频
            video = video.subclip(start_time, end_time)
            self.progress_bar.setValue(50)
            
            # 提取音频并添加淡出效果
            audio = video.audio
            
            # 添加0.5秒的淡出效果
            audio = audio.audio_fadeout(0.5)
            self.progress_bar.setValue(70)
            
            # 创建完整的输出文件路径
            filename = self.file_name_edit.text().strip()
            if not filename.endswith('.mp3'):
                filename += '.mp3'
            output_file_path = os.path.join(self.output_path, filename)
            
            # 使用高质量设置保存音频
            audio.write_audiofile(output_file_path, bitrate="320k", fps=44100, nbytes=4)
            self.progress_bar.setValue(100)
            
            # 关闭视频和音频对象
            video.close()
            audio.close()
            
            QMessageBox.information(self, '成功', f'高质量音频（带0.5秒淡出效果）已成功保存到 {output_file_path}')
            
        except Exception as e:
            QMessageBox.critical(self, '错误', f'转换过程中出错: {str(e)}')
        finally:
            # 重新启用按钮
            self.convert_btn.setEnabled(True)
    
    def time_to_mseconds(self, qtime):
        return qtime.hour() * 3600 + qtime.minute() * 60 + qtime.second() + qtime.msec() / 1000

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DouYinConverter()
    window.show()
    sys.exit(app.exec_()) 