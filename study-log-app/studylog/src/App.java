public class App {
    // ===== 設定 =====
    static final int MAX = 200;

    static final String[] SUBJECTS = { "Java", "数学", "英語", "その他" };
    static final String[] TYPES = { "インプット", "アウトプット", "復習" };

    // ===== 記録データ（配列）=====
    static String[] dates = new String[MAX];
    static int[] subjectIdx = new int[MAX];
    static int[] minutes = new int[MAX];
    static String[] memos = new String[MAX];
    static int[] typeIdx = new int[MAX];
    static int count = 0;

    public static void main(String[] args) throws Exception {
        java.util.Scanner sc = new java.util.Scanner(System.in);

        loop: while (true) {
            printMenu();
            int choice = inputIntInRange(sc, "番号を入力: ", 1, 5);

            switch (choice) {
                case 1 -> {
                    addRecord(sc);
                }
                case 2 -> {
                    listRecords();
                }
                case 3 -> {
                    showSummary();
                }
                case 4 -> {
                    System.out.println("保存/読み込みは拡張として後で実装します。");
                }
                case 5 -> {
                    System.out.println("終了します。おつかれさまでした！");
                    break loop;
                }
            }

            System.out.println();
        }

        sc.close();
    }

    // ===== 画面 =====
    static void printMenu() {
        System.out.println("==== 学習記録アプリ ====");
        System.out.println("1. 記録を追加");
        System.out.println("2. 記録一覧（新しい順）");
        System.out.println("3. 集計（総合計・科目別ランキング）");
        System.out.println("4. 保存/読み込み（未実装）");
        System.out.println("5. 終了");
    }

    // ===== 機能1：追加 =====
    static void addRecord(java.util.Scanner sc) {
        if (count >= MAX) {
            System.out.println("これ以上追加できません（最大 " + MAX + " 件）。");
            return;
        }

        String date = inputNonEmptyLine(sc, "日付(YYYY-MM-DD): ");
        int sIdx = chooseFromList(sc, "科目を選択", SUBJECTS);
        int mins = inputIntMin(sc, "学習時間(分): ", 1);
        String memo = inputLineAllowEmpty(sc, "メモ(空OK): ");
        int tIdx = chooseFromList(sc, "学習タイプを選択", TYPES);

        dates[count] = date;
        subjectIdx[count] = sIdx;
        minutes[count] = mins;
        memos[count] = memo;
        typeIdx[count] = tIdx;
        count++;

        System.out.println("追加しました。現在 " + count + " 件です。");
    }

    // ===== 機能2：一覧 =====
    static void listRecords() {
        if (count == 0) {
            System.out.println("記録がありません。まずは 1. 記録を追加 からどうぞ。");
            return;
        }

        System.out.println("---- 一覧（新しい順）----");
        for (int i = count - 1; i >= 0; i--) {
            System.out.println(
                    "#" + (i + 1) + " " + dates[i] +
                            " | " + SUBJECTS[subjectIdx[i]] +
                            " | " + minutes[i] + "分" +
                            " | " + TYPES[typeIdx[i]] +
                            " | " + memos[i]);

        }
    }

    // ===== 機能3：集計 =====
    static void showSummary() {
        if (count == 0) {
            System.out.println("記録がありません。集計できることがまだ何もありません");
            return;
        }

        int total = 0;
        int[] totalsBySubject = new int[SUBJECTS.length];

        for (int i = 0; i < count; i++) {
            total += minutes[i];
            totalsBySubject[subjectIdx[i]] += minutes[i];
        }

        System.out.println("---- 集計 ----");
        System.out.println("総学習時間: " + total + "分（" + (total / 60) + "時間" + (total % 60) + "分）");
        printSubjectRanking(totalsBySubject);
    }

    static void printSubjectRanking(int[] totalsBySubject) {
        int n = totalsBySubject.length;

        // 並べ替え用に「科目番号の配列」を作る（中身は 0,1,2,...）
        int[] order = new int[n];
        for (int i = 0; i < n; i++) {
            order[i] = i;
        }

        // 選択ソート：totalsBySubject が大きい順に order を並べ替える
        for (int i = 0; i < n - 1; i++) {
            int best = i;
            for (int j = i + 1; j < n; j++) {
                if (totalsBySubject[order[j]] > totalsBySubject[order[best]]) {
                    best = j;
                }
            }
            int tmp = order[i];
            order[i] = order[best];
            order[best] = tmp;
        }

        System.out.println("科目別ランキング:");
        for (int rank = 0; rank < n; rank++) {
            int s = order[rank];
            System.out.println((rank + 1) + "位: " + SUBJECTS[s] + " " + totalsBySubject[s] + "分");
        }
    }

    // ===== 入力ユーティリティ =====
    static int chooseFromList(java.util.Scanner sc, String title, String[] options) {
        System.out.println(title);
        for (int i = 0; i < options.length; i++) {
            System.out.println((i + 1) + ". " + options[i]);
        }
        return inputIntInRange(sc, "番号: ", 1, options.length) - 1;
    }

    // ※仕様：数字以外を入力しない前提
    static int inputIntInRange(java.util.Scanner sc, String prompt, int min, int max) {
        while (true) {
            System.out.print(prompt);
            int v = sc.nextInt();
            sc.nextLine(); // 改行を消費（次の nextLine のため）

            if (v < min || v > max) {
                System.out.println(min + "~" + max + " の範囲で入力してください。");
                continue;
            }
            return v;
        }
    }

    static int inputIntMin(java.util.Scanner sc, String prompt, int min) {
        while (true) {
            System.out.print(prompt);
            int v = sc.nextInt();
            sc.nextLine(); // 改行を消費

            if (v < min) {
                System.out.println(min + "以上で入力してください。");
                continue;
            }
            return v;
        }
    }

    static String inputNonEmptyLine(java.util.Scanner sc, String prompt) {
        while (true) {
            System.out.print(prompt);
            String s = sc.nextLine();

            if (s.length() == 0) {
                System.out.println("空は不可です。");
                continue;
            }
            return s;
        }
    }

    static String inputLineAllowEmpty(java.util.Scanner sc, String prompt) {
        System.out.print(prompt);
        return sc.nextLine();
    }
}