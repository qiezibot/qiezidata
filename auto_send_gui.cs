using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Runtime.InteropServices;
using System.Windows.Forms;
using Timer = System.Windows.Forms.Timer;

namespace AutoSend
{
    public class FloatMini : Form
    {
        [DllImport("user32.dll")]
        static extern bool keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);
        [DllImport("user32.dll")]
        static extern short GetAsyncKeyState(int vKey);

        const int VK_RETURN = 0x0D;
        const int KEYEVENTF_KEYUP = 0x0002;

        private bool _enabled = true;
        private bool _keyWasDown = false;
        private DateTime _lastRelease = DateTime.Now;
        private Timer _timer;
        private bool _dragging = false;
        private Point _dragStart;

        public FloatMini()
        {
            this.FormBorderStyle = FormBorderStyle.None;
            this.StartPosition = FormStartPosition.Manual;
            this.AutoSize = true;
            this.AutoSizeMode = AutoSizeMode.GrowAndShrink;
            this.Padding = new Padding(4, 3, 4, 3);

            var panel = new FlowLayoutPanel();
            panel.FlowDirection = FlowDirection.LeftToRight;
            panel.AutoSize = true;
            panel.AutoSizeMode = AutoSizeMode.GrowAndShrink;
            panel.BackColor = Color.Transparent;
            panel.WrapContents = false;

            var lbl = new Label();
            lbl.Text = "自动发送";
            lbl.Font = new Font("微软雅黑", 9, FontStyle.Bold);
            lbl.ForeColor = Color.White;
            lbl.AutoSize = true;
            lbl.Margin = new Padding(0);
            lbl.TextAlign = ContentAlignment.MiddleLeft;

            var toggle = new CheckBox();
            toggle.Text = "";
            toggle.AutoSize = false;
            toggle.Size = new Size(38, 20);
            toggle.Margin = new Padding(4, 0, 0, 0);
            toggle.Appearance = Appearance.Button;
            toggle.FlatStyle = FlatStyle.Flat;
            toggle.FlatAppearance.BorderSize = 0;
            toggle.Checked = true;

            toggle.Paint += (s, e) =>
            {
                var g = e.Graphics;
                g.SmoothingMode = SmoothingMode.AntiAlias;
                int w = toggle.Width, h = toggle.Height;
                Color bg = toggle.Checked ? Color.FromArgb(52, 199, 89) : Color.FromArgb(200, 200, 200);
                using (var path = new GraphicsPath())
                {
                    path.AddArc(0, 0, h, h, 90, 180);
                    path.AddArc(w - h, 0, h, h, 270, 180);
                    path.CloseFigure();
                    using (var brush = new SolidBrush(bg)) g.FillPath(brush, path);
                }
                int dotSize = h - 4;
                int dotX = toggle.Checked ? w - h + 2 : 2;
                using (var brush = new SolidBrush(Color.White))
                using (var pen = new Pen(Color.FromArgb(200, 200, 200), 1))
                {
                    g.FillEllipse(brush, dotX, 2, dotSize, dotSize);
                    g.DrawEllipse(pen, dotX, 2, dotSize, dotSize);
                }
            };

            toggle.CheckedChanged += (s, e) =>
            {
                _enabled = toggle.Checked;
                this.BackColor = _enabled ? Color.FromArgb(33, 150, 243) : Color.FromArgb(180, 180, 180);
                toggle.Invalidate();
            };

            panel.Controls.Add(lbl);
            panel.Controls.Add(toggle);
            this.Controls.Add(panel);
            this.BackColor = Color.FromArgb(33, 150, 243);
            this.TopMost = true;
            this.ShowInTaskbar = false;
            this.DoubleBuffered = true;
            SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.UserPaint | ControlStyles.ResizeRedraw | ControlStyles.OptimizedDoubleBuffer, true);
            UpdateStyles();

            this.Location = new Point(
                Screen.PrimaryScreen.WorkingArea.Width - this.PreferredSize.Width - 20,
                Screen.PrimaryScreen.WorkingArea.Height / 2 - this.PreferredSize.Height / 2);

            this.Paint += (s, e) =>
            {
                var g = e.Graphics;
                g.SmoothingMode = SmoothingMode.AntiAlias;
                using (var path = new GraphicsPath())
                {
                    path.AddArc(0, 0, 8, 8, 180, 90);
                    path.AddArc(Width - 8, 0, 8, 8, 270, 90);
                    path.AddArc(Width - 8, Height - 8, 8, 8, 0, 90);
                    path.AddArc(0, Height - 8, 8, 8, 90, 90);
                    path.CloseFigure();
                    Region = new Region(path);
                }
            };

            BindDrag(this);

            _timer = new Timer();
            _timer.Interval = 150;
            _timer.Tick += (s, e) =>
            {
                if (!_enabled) return;

                bool anyKey = false;
                for (int vk = 1; vk <= 254; vk++)
                {
                    if ((GetAsyncKeyState(vk) & 0x8000) != 0)
                    {
                        anyKey = true;
                        break;
                    }
                }

                if (anyKey)
                {
                    _keyWasDown = true;
                }
                else if (_keyWasDown)
                {
                    _lastRelease = DateTime.Now;
                    _keyWasDown = false;
                }

                if (!anyKey && !_keyWasDown && (DateTime.Now - _lastRelease).TotalSeconds >= 5)
                {
                    keybd_event(VK_RETURN, 0, 0, UIntPtr.Zero);
                    keybd_event(VK_RETURN, 0, KEYEVENTF_KEYUP, UIntPtr.Zero);
                    _lastRelease = DateTime.Now;
                    _keyWasDown = false;
                }
            };
            _timer.Start();
        }

        protected override void OnFormClosed(FormClosedEventArgs e)
        {
            if (_timer != null) _timer.Stop();
            base.OnFormClosed(e);
        }

        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new FloatMini());
        }
        private void BindDrag(Control c)
        {
            c.MouseDown += (s, e) => { _dragging = true; _dragStart = e.Location; };
            c.MouseMove += (s, e) =>
            {
                if (_dragging)
                {
                    this.Left += e.X - _dragStart.X;
                    this.Top += e.Y - _dragStart.Y;
                }
            };
            c.MouseUp += (s, e) => _dragging = false;
            foreach (Control child in c.Controls)
                BindDrag(child);
        }
    }
}
