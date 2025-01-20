using UnityEngine;
using System.Collections;
using UnityEngine.Networking;

public class ApiRequest : MonoBehaviour
{
    // APIにPOSTリクエストを送るメソッド
    public void SendPostRequest(string url, string jsonData)
    {
        StartCoroutine(PostRequest(url, jsonData));
    }

    // POSTリクエストを実行するCoroutine
    private IEnumerator PostRequest(string url, string jsonData)
    {
        // リクエストを作成
        UnityWebRequest request = new UnityWebRequest(url, "POST");
        byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(jsonData);
        request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");

        // リクエストを送信
        yield return request.SendWebRequest();

        // エラーチェック
        if (request.isNetworkError || request.isHttpError)
        {
            Debug.LogError("Error: " + request.error);
        }
        else
        {
            // 成功した場合のレスポンス
            Debug.Log("Response: " + request.downloadHandler.text);
        }
    }

    // 引数を設定するためのラップメソッド
    // public void OnClickSendPostRequest()
    // {
    //     Debug.Log("OnClickSendPostRequest");
    //     string url = "http://localhost:8000/hello"; // APIのURL
    //     string jsonData = "{\"key\": \"value\"}";  // 送信するJSONデータ

    //     SendPostRequest(url, jsonData);  // 引数を渡してSendPostRequestを呼び出す
    // }


    public GameObject targetObject; 

    public void OnClickSendPostRequest()
    {
        // Debug.Log("OnClickSendPostRequest");
        string url = "http://localhost:8000/play"; // APIのURL
        
        Vector3 objectPosition = targetObject.transform.position;
        // 例えば、x座標をボリュームに反映させる
        // int leftVol = Mathf.Clamp((int)objectPosition.x, 0, 100);  // x座標をボリュームに反映
        // int rightVol = Mathf.Clamp((int)objectPosition.z, 0, 100); // z座標をボリュームに反映

        int leftVol = Mathf.Clamp((int)objectPosition.x, 0, 100);  // x座標をボリュームに反映
        int rightVol = 10; // ハードコーディングで設定
        int decay = 10;  // ハードコーディングで設定
        int delayMs = 30; // ハードコーディングで設定
        int repeats = 30; // ハードコーディングで設定
        int leftDelay = 20; // ハードコーディングで設定
        int rightDelay = 0; // ハードコーディングで設定
        // int position = (int)objectPosition.y; // y座標を位置に反映
        int position = 10; // ハードコーディングで設定

        string jsonData = "{\n" +
                          $"    \"left_vol\": {leftVol},\n" +
                          $"    \"right_vol\": {rightVol},\n" +
                          $"    \"decay\": {decay},\n" +
                          $"    \"delay_ms\": {delayMs},\n" +
                          $"    \"repeats\": {repeats},\n" +
                          $"    \"left_delay\": {leftDelay},\n" +
                          $"    \"right_delay\": {rightDelay},\n" +
                          $"    \"position\": {position}\n" +
                          "}";  // 送信するJSONデータ

        SendPostRequest(url, jsonData);  // 引数を渡してSendPostRequestを呼び出す
    }


}
