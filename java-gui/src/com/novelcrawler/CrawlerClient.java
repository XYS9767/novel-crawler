package com.novel.crawler;

import com.fasterxml.jackson.databind.ObjectMapper;
import okhttp3.*;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.TimeUnit;

public class CrawlerClient {
    private static final String BASE_URL = "http://localhost:5000/api";
    private final OkHttpClient client;
    private final ObjectMapper mapper;
    private final MainFrame mainFrame;
    private boolean isRunning = false;

    public CrawlerClient(MainFrame mainFrame) {
        this.mainFrame = mainFrame;
        this.client = new OkHttpClient.Builder()
                .connectTimeout(30, TimeUnit.SECONDS)
                .readTimeout(30, TimeUnit.SECONDS)
                .build();
        this.mapper = new ObjectMapper();
    }

    public void startCrawling(String novelName, String ranking, int startPage, int endPage, String savePath) {
        if (isRunning) {
            mainFrame.appendLog("爬取任务正在进行中...");
            return;
        }

        isRunning = true;
        new Thread(() -> {
            try {
                // 构建请求参数
                Map<String, Object> requestData = new HashMap<>();
                requestData.put("novel_name", novelName);
                requestData.put("ranking", ranking);
                requestData.put("start_page", startPage);
                requestData.put("end_page", endPage);
                requestData.put("save_path", savePath);

                String json = mapper.writeValueAsString(requestData);
                RequestBody body = RequestBody.create(json, MediaType.parse("application/json"));

                Request request = new Request.Builder()
                        .url(BASE_URL + "/start")
                        .post(body)
                        .build();

                mainFrame.appendLog("开始爬取任务...");
                mainFrame.appendLog("目标小说: " + novelName);
                mainFrame.appendLog("榜单类型: " + ranking);
                mainFrame.appendLog("页码范围: " + startPage + " - " + endPage);

                try (Response response = client.newCall(request).execute()) {
                    if (response.isSuccessful()) {
                        String responseBody = response.body().string();
                        Map<String, Object> result = mapper.readValue(responseBody, Map.class);
                        if ("success".equals(result.get("status"))) {
                            mainFrame.appendLog("爬取任务启动成功");
                            // 开始轮询进度
                            pollProgress();
                        } else {
                            mainFrame.appendLog("启动失败: " + result.get("message"));
                        }
                    } else {
                        mainFrame.appendLog("HTTP请求失败: " + response.code());
                    }
                }
            } catch (Exception e) {
                mainFrame.appendLog("启动爬取任务时发生错误: " + e.getMessage());
                isRunning = false;
                mainFrame.crawlingFinished();
            }
        }).start();
    }

    private void pollProgress() {
        new Thread(() -> {
            while (isRunning) {
                try {
                    Request request = new Request.Builder()
                            .url(BASE_URL + "/progress")
                            .get()
                            .build();

                    try (Response response = client.newCall(request).execute()) {
                        if (response.isSuccessful()) {
                            String responseBody = response.body().string();
                            Map<String, Object> progress = mapper.readValue(responseBody, Map.class);
                            
                            int currentProgress = (int) progress.get("progress");
                            String message = (String) progress.get("message");
                            String currentTask = (String) progress.get("current_task");
                            
                            mainFrame.updateProgress(currentProgress, message);
                            mainFrame.appendLog(currentTask);

                            if (currentProgress >= 100 || "completed".equals(progress.get("status"))) {
                                mainFrame.appendLog("爬取任务已完成");
                                isRunning = false;
                                mainFrame.crawlingFinished();
                                break;
                            }

                            if ("error".equals(progress.get("status"))) {
                                mainFrame.appendLog("爬取任务出错: " + progress.get("message"));
                                isRunning = false;
                                mainFrame.crawlingFinished();
                                break;
                            }
                        }
                    }

                    Thread.sleep(1000); // 每秒轮询一次
                } catch (Exception e) {
                    mainFrame.appendLog("获取进度时发生错误: " + e.getMessage());
                    try {
                        Thread.sleep(5000); // 出错后等待5秒再重试
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                    }
                }
            }
        }).start();
    }

    public void stopCrawling() {
        if (!isRunning) return;

        new Thread(() -> {
            try {
                Request request = new Request.Builder()
                        .url(BASE_URL + "/stop")
                        .post(RequestBody.create("", MediaType.parse("application/json")))
                        .build();

                try (Response response = client.newCall(request).execute()) {
                    if (response.isSuccessful()) {
                        mainFrame.appendLog("已发送停止信号");
                    }
                }
            } catch (Exception e) {
                mainFrame.appendLog("停止爬取任务时发生错误: " + e.getMessage());
            } finally {
                isRunning = false;
            }
        }).start();
    }

    public boolean checkServerStatus() {
        try {
            Request request = new Request.Builder()
                    .url(BASE_URL + "/status")
                    .get()
                    .build();

            try (Response response = client.newCall(request).execute()) {
                return response.isSuccessful();
            }
        } catch (Exception e) {
            return false;
        }
    }
}