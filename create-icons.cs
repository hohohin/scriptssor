using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Text;
using System.IO;

class Program
{
    static void Main()
    {
        // 创建不同尺寸的图标
        int[] sizes = { 16, 32, 48, 128 };
        
        foreach (int size in sizes)
        {
            CreateIcon(size);
        }
        
        Console.WriteLine("PNG icons created successfully!");
    }
    
    static void CreateIcon(int size)
    {
        // 创建位图
        using (Bitmap bitmap = new Bitmap(size, size))
        using (Graphics graphics = Graphics.FromImage(bitmap))
        {
            // 设置高质量渲染
            graphics.SmoothingMode = SmoothingMode.AntiAlias;
            graphics.TextRenderingHint = TextRenderingHint.AntiAlias;
            graphics.CompositingQuality = CompositingQuality.HighQuality;
            
            // 创建渐变背景
            using (LinearGradientBrush brush = new LinearGradientBrush(
                new Rectangle(0, 0, size, size),
                ColorTranslator.FromHtml("#3b82f6"),
                ColorTranslator.FromHtml("#8b5cf6"),
                LinearGradientMode.ForwardDiagonal))
            {
                graphics.FillRectangle(brush, 0, 0, size, size);
            }
            
            // 计算圆角半径
            int cornerRadius = (int)(size * 0.2);
            
            // 创建圆角路径
            using (GraphicsPath path = new GraphicsPath())
            {
                path.AddArc(0, 0, cornerRadius * 2, cornerRadius * 2, 180, 90);
                path.AddArc(size - cornerRadius * 2, 0, cornerRadius * 2, cornerRadius * 2, 270, 90);
                path.AddArc(size - cornerRadius * 2, size - cornerRadius * 2, cornerRadius * 2, cornerRadius * 2, 0, 90);
                path.AddArc(0, size - cornerRadius * 2, cornerRadius * 2, cornerRadius * 2, 90, 90);
                path.CloseAllFigures();
                
                // 应用圆角遮罩
                using (Region region = new Region(bitmap.GetBounds()))
                {
                    region.Intersect(path);
                    graphics.SetClip(region, CombineMode.Replace);
                    
                    // 重新绘制渐变背景
                    using (LinearGradientBrush brush = new LinearGradientBrush(
                        new Rectangle(0, 0, size, size),
                        ColorTranslator.FromHtml("#3b82f6"),
                        ColorTranslator.FromHtml("#8b5cf6"),
                        LinearGradientMode.ForwardDiagonal))
                    {
                        graphics.FillRectangle(brush, 0, 0, size, size);
                    }
                }
            }
            
            // 绘制文字
            using (Font font = new Font("Arial", (int)(size * 0.6), FontStyle.Bold))
            using (SolidBrush textBrush = new SolidBrush(Color.White))
            using (StringFormat stringFormat = new StringFormat()
            {
                Alignment = StringAlignment.Center,
                LineAlignment = StringAlignment.Center
            })
            {
                graphics.DrawString("S", font, textBrush, size / 2f, size / 2f, stringFormat);
            }
            
            // 保存为PNG
            string outputPath = Path.Combine(Directory.GetCurrentDirectory(), "browser-extension-store", "icons", $"icon{size}.png");
            bitmap.Save(outputPath, System.Drawing.Imaging.ImageFormat.Png);
            
            Console.WriteLine($"Created: {outputPath}");
        }
    }
}