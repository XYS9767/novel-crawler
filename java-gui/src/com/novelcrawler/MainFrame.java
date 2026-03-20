package com.novelcrawler;

import javax.swing.*;
import javax.swing.border.TitledBorder;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.prefs.Preferences;

public class MainFrame extends JFrame {
    private JTextField novelNameField;
    private JComboBox<String> rankingComboBox;
    private JSpinner startPageSpinner;
    private JSpinner endPageSpinner;
    private JProgressBar progressBar;
    private JTextArea logArea;
    private JButton startButton;
    private JButton stopButton;
    private JTextField savePathField;
    
    private CrawlerClient crawlerClient;
    private Preferences prefs;

    public MainFrame() {
        initComponents();
        loadPreferences();
        crawlerClient = new CrawlerClient();
    }

    private void initComponents() {
        setTitle("番茄小说爬取工具 - Java GUI");
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setSize(900, 700);
        setLocationRelativeTo(null);

        // 主面板
        JPanel mainPanel = new JPanel(new BorderLayout(10, 10));
        mainPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        // 搜索设置面板
        JPanel searchPanel = createSearchPanel();
        mainPanel.add(searchPanel, BorderLayout.NORTH);

        // 进度显示面板
        JPanel progressPanel = createProgressPanel();
        mainPanel.add(progressPanel, BorderLayout.CENTER);

        // 日志面板
        JPanel logPanel = createLogPanel();
        mainPanel.add(logPanel, BorderLayout.SOUTH);

        add(mainPanel);
    }

    private JPanel createSearchPanel() {
        JPanel panel = new JPanel(new GridBagLayout());
        panel.setBorder(BorderFactory.createTitledBorder("爬取设置"));
        
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(5, 5, 5, 5);
        gbc.fill = GridBagConstraints.HORIZONTAL;

        // 小说名称
        gbc.gridx = 0; gbc.gridy = 0; gbc.weightx = 0;
        panel.add(new JLabel("小说名称:"), gbc);
        
        gbc.gridx = 1; gbc.weightx = 1.0;
        novelNameField = new JTextField(20);
        panel.add(novelNameField, gbc);

        // 榜单选择
        gbc.gridx = 0; gbc.gridy = 1; gbc.weightx = 0;
        panel.add(new JLabel("选择榜单:"), gbc);
        
        gbc.gridx = 1; gbc.weightx = 1.0;
        String[] rankings = {"全部", "热搜榜", "飙升榜", "完结榜", "新书榜"};
        rankingComboBox = new JComboBox<>(rankings);
        panel.add(rankingComboBox, gbc);

        // 页码设置
        gbc.gridx = 0; gbc.gridy = 2; gbc.weightx = 0;
        panel.add(new JLabel("起始页:"), gbc);
        
        gbc.gridx = 1; gbc.weightx = 0.3;
        startPageSpinner = new JSpinner(new SpinnerNumberModel(1, 1, 100, 1));
        panel.add(startPageSpinner, gbc);

        gbc.gridx = 2; gbc.weightx = 0;
        panel.add(new JLabel("结束页:"), gbc);
        
        gbc.gridx = 3; gbc.weightx = 0.3;
        endPageSpinner = new JSpinner(new SpinnerNumberModel(10, 1, 100, 1));
        panel.add(endPageSpinner, gbc);

        // 保存路径
        gbc.gridx = 0; gbc.gridy = 3; gbc.weightx = 0;
        panel.add(new JLabel("保存路径:"), gbc);
        
        gbc.gridx = 1; gbc.gridwidth = 3; gbc.weightx = 1.0;
        savePathField = new JTextField(System.getProperty("user.home") + "/novels/");
        panel.add(savePathField, gbc);

        // 按钮面板
        gbc.gridx = 0; gbc.gridy = 4; gbc.gridwidth = 4; gbc.weightx = 1.0;
        JPanel buttonPanel = new JPanel(new FlowLayout(FlowLayout.CENTER));
        
        startButton = new JButton("开始爬取");
        startButton.addActionListener(new StartButtonListener());
        buttonPanel.add(startButton);
        
        stopButton = new JButton("停止爬取");
        stopButton.setEnabled(false);
        stopButton.addActionListener(new StopButtonListener());
        buttonPanel.add(stopButton);
        
        panel.add(buttonPanel, gbc);

        return panel;
    }

    private JPanel createProgressPanel() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBorder(BorderFactory.createTitledBorder("爬取进度"));
        
        progressBar = new JProgressBar(0, 100);
        progressBar.setStringPainted(true);
        panel.add(progressBar, BorderLayout.CENTER);
        
        return panel;
    }

    private JPanel createLogPanel() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBorder(BorderFactory.createTitledBorder("爬取日志"));
        panel.setPreferredSize(new Dimension(800, 300));
        
        logArea = new JTextArea();
        logArea.setEditable(false);
        JScrollPane scrollPane = new JScrollPane(logArea);
        panel.add(scrollPane, BorderLayout.CENTER);
        
        return panel;
    }

    private class StartButtonListener implements ActionListener {
        @Override
        public void actionPerformed(ActionEvent e) {
            String novelName = novelNameField.getText().trim();
            if (novelName.isEmpty()) {
                JOptionPane.showMessageDialog(MainFrame.this, "请输入小说名称");
                return;
            }
            
            int startPage = (Integer) startPageSpinner.getValue();
            int endPage = (Integer) endPageSpinner.getValue();
            if (startPage > endPage) {
                JOptionPane.showMessageDialog(MainFrame.this, "起始页不能大于结束页");
                return;
            }
            
            savePreferences();
            startButton.setEnabled(false);
            stopButton.setEnabled(true);
            
            // 启动爬取线程
            new CrawlerThread(novelName, startPage, endPage).start();
        }
    }

    private class StopButtonListener implements ActionListener {
        @Override
        public void actionPerformed(ActionEvent e) {
            crawlerClient.stopCrawling();
            stopButton.setEnabled(false);
            startButton.setEnabled(true);
            logMessage("爬取已停止");
        }
    }

    private class CrawlerThread extends Thread {
        private String novelName;
        private int startPage;
        private int endPage;

        public CrawlerThread(String novelName, int startPage, int endPage) {
            this.novelName = novelName;
            this.startPage = startPage;
            this.endPage = endPage;
        }

        @Override
        public void run() {
            try {
                String ranking = (String) rankingComboBox.getSelectedItem();
                String savePath = savePathField.getText();
                
                crawlerClient.startCrawling(novelName, ranking, startPage, endPage, savePath, 
                    new CrawlerClient.CrawlerCallback() {
                        @Override
                        public void onProgress(int current, int total, String message) {
                            SwingUtilities.invokeLater(() -> {
                                int progress = (int) ((double) current / total * 100);
                                progressBar.setValue(progress);
                                progressBar.setString(message);
                            });
                        }

                        @Override
                        public void onLog(String message) {
                            SwingUtilities.invokeLater(() -> logMessage(message));
                        }

                        @Override
                        public void onComplete() {
                            SwingUtilities.invokeLater(() -> {
                                startButton.setEnabled(true);
                                stopButton.setEnabled(false);
                                progressBar.setValue(100);
                                progressBar.setString("爬取完成");
                            });
                        }

                        @Override
                        public void onError(String error) {
                            SwingUtilities.invokeLater(() -> {
                                logMessage("错误: " + error);
                                startButton.setEnabled(true);
                                stopButton.setEnabled(false);
                            });
                        }
                    });
                    
            } catch (Exception ex) {
                SwingUtilities.invokeLater(() -> {
                    logMessage("爬取错误: " + ex.getMessage());
                    startButton.setEnabled(true);
                    stopButton.setEnabled(false);
                });
            }
        }
    }

    private void logMessage(String message) {
        logArea.append("[" + java.time.LocalTime.now() + "] " + message + "\n");
        logArea.setCaretPosition(logArea.getDocument().getLength());
    }

    private void loadPreferences() {
        prefs = Preferences.userNodeForPackage(MainFrame.class);
        novelNameField.setText(prefs.get("novelName", ""));
        savePathField.setText(prefs.get("savePath", System.getProperty("user.home") + "/novels/"));
    }

    private void savePreferences() {
        prefs.put("novelName", novelNameField.getText());
        prefs.put("savePath", savePathField.getText());
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            try {
                UIManager.setLookAndFeel(UIManager.getSystemLookAndFeel());
            } catch (Exception e) {
                e.printStackTrace();
            }
            new MainFrame().setVisible(true);
        });
    }
}