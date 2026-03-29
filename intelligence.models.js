const mongoose = require("mongoose");

const IntelligenceEntrySchema = new mongoose.Schema({
  title: { type: String, required: true },
  rationale: { type: String, required: true },
});

const IntelligenceSchema = new mongoose.Schema({
  date: { type: Date, default: Date.now },
  threats: { type: [IntelligenceEntrySchema], default: [] },
  opportunities: { type: [IntelligenceEntrySchema], default: [] },
  trends: { type: [IntelligenceEntrySchema], default: [] },
});

module.exports = mongoose.model("Intelligence", IntelligenceSchema);
