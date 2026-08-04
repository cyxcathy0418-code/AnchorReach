"use client";

import React, { useMemo, useState } from "react";
import { FiAlertCircle, FiPlus, FiTrash2, FiZap } from "react-icons/fi";

const MARKET_OPTIONS = [
  { market_code: "US", language: "en", label: "United States · English" },
  { market_code: "DE", language: "de", label: "Germany · Deutsch" },
  { market_code: "JP", language: "ja", label: "Japan · 日本語" },
  { market_code: "KR", language: "ko", label: "South Korea · 한국어" },
  { market_code: "AE", language: "ar", label: "UAE · العربية (RTL)" },
];

const DEFAULT_MARKET = MARKET_OPTIONS[0];

const splitLines = (value) =>
  value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);

export default function StructuredCampaignForm({
  onSubmit,
  busy = false,
  uploadedImages = [],
  errors = [],
}) {
  const [brandName, setBrandName] = useState("");
  const [category, setCategory] = useState("");
  const [sellingPoints, setSellingPoints] = useState("");
  const [imageSources, setImageSources] = useState("");
  const [logoUrl, setLogoUrl] = useState("");
  const [primaryColor, setPrimaryColor] = useState("");
  const [campaignType, setCampaignType] = useState("poster");
  const [markets, setMarkets] = useState([{ ...DEFAULT_MARKET }]);

  const uploadedImageUrls = useMemo(
    () => [...new Set(uploadedImages.map((image) => image.url).filter(Boolean))],
    [uploadedImages],
  );

  const updateMarket = (index, field, value) => {
    const selectedPreset = field === "market_code"
      ? MARKET_OPTIONS.find((option) => option.market_code === value)
      : null;
    setMarkets((current) =>
      current.map((market, marketIndex) =>
        marketIndex === index
          ? {
              ...market,
              [field]: value,
              ...(selectedPreset ? { language: selectedPreset.language } : {}),
            }
          : market,
      ),
    );
  };

  const addMarket = () => {
    const selectedCodes = new Set(markets.map((market) => market.market_code));
    const nextMarket = MARKET_OPTIONS.find((option) => !selectedCodes.has(option.market_code));
    if (nextMarket) setMarkets((current) => [...current, { ...nextMarket }]);
  };

  const removeMarket = (index) => {
    setMarkets((current) => current.filter((_, marketIndex) => marketIndex !== index));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    const images = [...new Set([...uploadedImageUrls, ...splitLines(imageSources)])];
    onSubmit({
      product: {
        category,
        core_selling_points: splitLines(sellingPoints),
        images,
        brand_name: brandName,
        ...(logoUrl.trim() ? { logo_url: logoUrl.trim() } : {}),
        ...(primaryColor.trim() ? { primary_color: primaryColor.trim() } : {}),
      },
      target_markets: markets.map(({ market_code, language }) => ({ market_code, language })),
      campaign_type: campaignType,
    });
  };

  const inputClass =
    "w-full rounded border border-divider bg-bg-page px-2.5 py-2 text-[12px] text-primary-text outline-none transition focus:border-primary";

  return (
    <form onSubmit={handleSubmit} className="max-h-[58vh] overflow-y-auto p-3 scrollbar-subtle">
      <div className="mb-3">
        <div className="flex items-center gap-2 text-[12px] font-bold text-primary-text">
          <FiZap className="text-primary" /> AnchorReach campaign brief
        </div>
        <p className="mt-1 text-[10px] leading-relaxed text-secondary-text">
          Validate anchors and apply a curated market brief before the design agent starts. Choose up to three markets per campaign.
        </p>
      </div>

      {errors.length > 0 && (
        <div className="mb-3 rounded border border-red-500/40 bg-red-500/10 p-2.5" role="alert">
          {errors.map((error, index) => (
            <div key={`${error.field}-${index}`} className="flex items-start gap-2 text-[10px] text-red-500">
              <FiAlertCircle className="mt-0.5 shrink-0" />
              <span><strong>{error.field}</strong>: {error.reason}</span>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-2 gap-2">
        <label className="text-[10px] font-semibold text-secondary-text">
          Brand name *
          <input className={`${inputClass} mt-1`} value={brandName} onChange={(event) => setBrandName(event.target.value)} required />
        </label>
        <label className="text-[10px] font-semibold text-secondary-text">
          Product category *
          <input className={`${inputClass} mt-1`} value={category} onChange={(event) => setCategory(event.target.value)} placeholder="wireless earbuds" required />
        </label>
      </div>

      <label className="mt-2 block text-[10px] font-semibold text-secondary-text">
        Core selling points * <span className="font-normal opacity-70">(one per line)</span>
        <textarea className={`${inputClass} mt-1 min-h-20 resize-y`} value={sellingPoints} onChange={(event) => setSellingPoints(event.target.value)} required />
      </label>

      <label className="mt-2 block text-[10px] font-semibold text-secondary-text">
        Product image URLs or server paths * <span className="font-normal opacity-70">(one per line)</span>
        <textarea
          className={`${inputClass} mt-1 min-h-16 resize-y`}
          value={imageSources}
          onChange={(event) => setImageSources(event.target.value)}
          required={uploadedImageUrls.length === 0}
          placeholder={uploadedImageUrls.length ? `${uploadedImageUrls.length} uploaded image(s) will be included` : "https://… or /absolute/path/to/image.png"}
        />
      </label>

      {uploadedImageUrls.length > 0 && (
        <div className="mt-1 text-[10px] text-green-500">
          {uploadedImageUrls.length} uploaded product image(s) attached to this brief.
        </div>
      )}

      <div className="mt-2 grid grid-cols-2 gap-2">
        <label className="text-[10px] font-semibold text-secondary-text">
          Logo URL/path <span className="font-normal opacity-70">(optional)</span>
          <input className={`${inputClass} mt-1`} value={logoUrl} onChange={(event) => setLogoUrl(event.target.value)} />
        </label>
        <label className="text-[10px] font-semibold text-secondary-text">
          Primary color <span className="font-normal opacity-70">(optional)</span>
          <input
            className={`${inputClass} mt-1`}
            value={primaryColor}
            onChange={(event) => setPrimaryColor(event.target.value)}
            pattern="#[0-9A-Fa-f]{6}"
            placeholder="#2455B4"
          />
        </label>
      </div>

      <label className="mt-2 block text-[10px] font-semibold text-secondary-text">
        Campaign type *
        <select className={`${inputClass} mt-1`} value={campaignType} onChange={(event) => setCampaignType(event.target.value)}>
          <option value="poster">Poster</option>
          <option value="social_post">Social post</option>
          <option value="ad_banner">Ad banner</option>
        </select>
      </label>

      <div className="mt-3 flex items-center justify-between">
        <span className="text-[10px] font-semibold text-secondary-text">Target markets *</span>
        <button
          type="button"
          onClick={addMarket}
          disabled={markets.length >= 3 || markets.length >= MARKET_OPTIONS.length}
          className="flex items-center gap-1 text-[10px] font-semibold text-primary disabled:cursor-not-allowed disabled:opacity-40"
        >
          <FiPlus /> Add market
        </button>
      </div>

      <div className="mt-1 space-y-1.5">
        {markets.map((market, index) => (
          <div key={index} className="grid grid-cols-[1fr_72px_auto] gap-1.5">
            <select
              aria-label={`Market ${index + 1}`}
              className={inputClass}
              value={market.market_code}
              onChange={(event) => updateMarket(index, "market_code", event.target.value)}
              required
            >
              {MARKET_OPTIONS.map((option) => (
                <option
                  key={option.market_code}
                  value={option.market_code}
                  disabled={markets.some((item, marketIndex) => marketIndex !== index && item.market_code === option.market_code)}
                >
                  {option.label}
                </option>
              ))}
            </select>
            <select
              aria-label={`Market ${index + 1} language`}
              className={inputClass}
              value={market.language}
              onChange={(event) => updateMarket(index, "language", event.target.value)}
              required
            >
              {market.market_code === "AE" ? (
                <>
                  <option value="ar">AR</option>
                  <option value="en">EN</option>
                </>
              ) : (
                <option value={MARKET_OPTIONS.find((option) => option.market_code === market.market_code)?.language || market.language}>
                  {market.language.toUpperCase()}
                </option>
              )}
            </select>
            <button
              type="button"
              onClick={() => removeMarket(index)}
              disabled={markets.length === 1}
              className="rounded border border-divider px-2 text-secondary-text hover:border-red-500 hover:text-red-500 disabled:cursor-not-allowed disabled:opacity-30"
              aria-label={`Remove market ${index + 1}`}
            >
              <FiTrash2 size={12} />
            </button>
          </div>
        ))}
      </div>

      <button
        type="submit"
        disabled={busy}
        className="mt-3 flex w-full items-center justify-center gap-2 rounded bg-primary px-3 py-2.5 text-[11px] font-bold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <FiZap /> {busy ? "Preparing market briefs…" : "Validate, localize, and run agent"}
      </button>

      <p className="mt-2 text-[9px] leading-relaxed text-secondary-text opacity-80">
        Compliance prompts are publication-review reminders, not legal clearance. Prices, discounts, certifications, and performance claims are never invented.
      </p>
    </form>
  );
}
