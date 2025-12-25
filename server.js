const express = require("express");
const cors = require("cors");
const { exec } = require("child_process");
const admin = require("firebase-admin");
const fs = require("fs");

const app = express();
app.use(cors());
app.use(express.json());

// 🔐 Firebase Admin Init
const serviceAccount = JSON.parse(
  fs.readFileSync("./firebase-admin.json", "utf8")
);

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});

const db = admin.firestore();

// 🚀 API
app.post("/analyze", (req, res) => {
  const { policyText } = req.body;

  exec(
    `python -c "from orchestrator import run_clarity; import json; print(json.dumps(run_clarity('''${policyText.replace(/'/g, "\\'")}''')))"`,
    async (err, stdout) => {
      if (err) {
        return res.status(500).json({ error: err.message });
      }

      try {
        const result = JSON.parse(stdout);

        // 🔥 Store in Firebase
        const docRef = await db.collection("clarity_outputs").add({
          policyText,
          result,
          critical: result.summary.critical,
          warnings: result.summary.warnings,
          createdAt: new Date()
        });

        res.json({
          firebase_id: docRef.id,
          result
        });

      } catch (e) {
        res.status(500).json({
          error: "Invalid JSON from Python",
          raw: stdout
        });
      }
    }
  );
});

app.listen(5000, () => {
  console.log("🔥 Server running on http://localhost:5000");
});
