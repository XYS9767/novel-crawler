package com.novel.crawler;

import java.util.prefs.Preferences;

public class ConfigManager {
    private static final String PREFS_NODE = "com/novel/crawler";
    private static final String KEY_NOVEL_NAME = "novel_name";
    private static final String KEY_RANKING = "ranking";
    private static final String KEY_START_PAGE = "start_page";
    private static final String KEY_END_PAGE = "end_page";
    private static final String KEY_SAVE_PATH = "save_path";

    private Preferences prefs;

    public ConfigManager() {
        prefs = Preferences.userRoot().node(PREFS_NODE);
    }

    public void saveConfig(String novelName, String ranking, int startPage, int endPage, String savePath) {
        prefs.put(KEY_NOVEL_NAME, novelName);
        prefs.put(KEY_RANKING, ranking);
        prefs.putInt(KEY_START_PAGE, startPage);
        prefs.putInt(KEY_END_PAGE, endPage);
        prefs.put(KEY_SAVE_PATH, savePath);
    }

    public Config loadConfig() {
        Config config = new Config();
        config.setNovelName(prefs.get(KEY_NOVEL_NAME, ""));
        config.setRanking(prefs.get(KEY_RANKING, "热搜榜"));
        config.setStartPage(prefs.getInt(KEY_START_PAGE, 1));
        config.setEndPage(prefs.getInt(KEY_END_PAGE, 10));
        config.setSavePath(prefs.get(KEY_SAVE_PATH, System.getProperty("user.home") + "/novels/"));
        return config;
    }

    public static class Config {
        private String novelName;
        private String ranking;
        private int startPage;
        private int endPage;
        private String savePath;

        // getters and setters
        public String getNovelName() { return novelName; }
        public void setNovelName(String novelName) { this.novelName = novelName; }
        
        public String getRanking() { return ranking; }
        public void setRanking(String ranking) { this.ranking = ranking; }
        
        public int getStartPage() { return startPage; }
        public void setStartPage(int startPage) { this.startPage = startPage; }
        
        public int getEndPage() { return endPage; }
        public void setEndPage(int endPage) { this.endPage = endPage; }
        
        public String getSavePath() { return savePath; }
        public void setSavePath(String savePath) { this.savePath = savePath; }
    }
}