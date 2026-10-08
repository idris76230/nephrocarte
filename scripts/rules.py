"""Règles partagées : filtre néphro / oncologie, thématiques, détection PHRC."""
import re
ONCO = re.compile(r"(renal|kidney)\s+(\w+\s+){0,2}(carcinoma|cancer|tumou?r|neoplasm)|clear cell|renal cell|kidney cancer|renal cancer|kidney neoplasm|renal neoplasm|tumou?ral kidney|wilms|nephroblastoma|carcinoma|cancer|tumou?r|neoplasm|melanoma|sarcoma|lymphoma|leuka?emia|glioma|blastoma|malignan", re.I)
NEPH = re.compile(r"kidney|renal|(?<!epi)nephr|glomerul|dialys|uremi|uraemi|\bckd\b|\baki\b|\besrd\b|\beskd\b|iga\b|alport|fabry|cystinosis|fsgs|hyperoxaluria|lithiasis|kidney stone|\bc3g\b|\bahus\b|hemolytic uremic|anca|polyangiitis|hyperkal|proteinuri|albuminuri|tubulopath|hypophosphat|gitelman|bartter|thrombotic microangiopath|cystinuria|hemodiafiltration|hemofiltration|renal replacement|minimal change|podocyt|hepatorenal|nephrotox|urolog|bladder dysfunction|enuresis|adpkd|polycystic|vasculitis|rejection|organ transplant|(?<!pulmonary )(?<!portal )hypertension|ureter|dialytic", re.I)
# études d'oncologie qui passent le filtre néphro (cancer du rein ou des voies urinaires, tumeurs solides « avec atteinte rénale »...) :
# écartées sauf question néphrologique explicite (néphrotoxicité, IRA, dialyse, biopsie rénale, greffe...)
ONCO_T = re.compile(r"cancer|carcinom|tumou?r|tumeur|neoplasm|néoplas|metasta|métasta|oncolog|malignan|lymphom|leuk[ae]?emi|sarcom|melanom|glioma|"
                    r"\bm?crpc\b|\bp?rcc\b|urothel|urothél", re.I)
ONCO_KEEP = re.compile(r"nephrotox|néphrotox|acute kidney|\baki\b|insuffisance rénale aigu|dialys|renal biopsy|biopsie rénale|nephrit|néphrit|"
                       r"glomerul|glomérul|onco-?neph|renal failure|kidney failure|renal impairment|insuffisance rénale|tumou?r lysis|lyse tumorale|cast nephropathy|microangiopath|transplant|greff|hyperkal", re.I)
def onco_study(*texts):
    t = " | ".join(x for x in texts if x)
    return bool(ONCO_T.search(t)) and not ONCO_KEEP.search(t)

def stale_ok(sm):
    """Fiche « UNKNOWN » (non mise à jour depuis plus de 2 ans) : gardée « À confirmer » si sa fin prévue est 2023 ou après
    (beaucoup d'études académiques ne sont jamais mises à jour), écartée si elle est plus ancienne."""
    fin = (sm.get("completionDateStruct") or sm.get("primaryCompletionDateStruct") or {}).get("date", "")
    return fin >= "2023" if fin else sm.get("startDateStruct", {}).get("date", "") >= "2019"
def txt(*xs): return " | ".join(x for x in xs if x)
THEMES = [
 ("Transplantation", r"transplant|graft|allograft|rejection|donor|recipient|desensiti|greff|donneur|rejet"),
 ("Dialyse / suppléance", r"dialys|hemodiafiltration|haemodiafiltration|end[- ]stage|\besrd\b|\beskd\b|kidney failure|renal replacement|arteriovenous fistula|vascular access|uremic pruritus|hémodiaf|suppléance|abord vasculaire"),
 ("Insuffisance rénale aiguë", r"acute kidney injury|\baki\b|acute renal|contrast[- ]induced|cardiac surgery associated|rhabdomyolysis|insuffisance rénale aigu|\bIRA\b|reins au cours du sepsis|néphroprotection"),
 ("Glomérulopathies / néphropathies immunes", r"glomerul|iga nephropathy|immunoglobulin a nephropathy|lupus nephritis|membranous|fsgs|nephrotic|minimal change|anca|polyangiitis|vasculitis|c3g|c3 glomerulopathy|hemolytic uremic|\bahus\b|thrombotic microangiopath|anti-gbm|goodpasture|complement|cryoglobulin|glomérul|néphropathie à iga|\bIgA\b|lupique|extramembraneuse|néphrotique|\bGEM\b|\bSHU\b|microangiopathie|vascularite|nephritogenic"),
 ("Maladies rénales rares / génétiques", r"polycystic|adpkd|alport|fabry|cystinosis|hyperoxaluria|cystinuria|gitelman|bartter|tubulopath|hypophosphat|nephronophthisis|apol1|genetic|hereditary|rare"),
 ("MRC / néphroprotection / cardio-rénal", r"chronic kidney|\bckd\b|chronic renal|renal insufficiency|diabetic kidney|diabetic nephropathy|albuminuri|proteinuri|hyperkal|anemia|anaemia|hypertension|cardio|heart failure|mineral|phosph|hyperparathyroid|metabolic acidosis|sglt2|finerenone|maladie rénale chronique|\bMRC\b|\bDFG\b|gliflozin|hyperkali|anémie|hyperparathyro"),
 ("Lithiase / infections urinaires", r"lithiasis|kidney stone|renal colic|pyelonephritis|urinary tract infection|lithiase|lithotri|residual fragment|fragments résiduels|pyélonéphrite|infection urinaire"),
]
def theme(t):
    r = [n for n, p in THEMES if re.search(p, t, re.I)]
    return r or ["Autre néphrologie"]
PHRC = re.compile(r"phrc|programme hospitalier de recherche|hospital clinical research program|prme|preps|phrip|dgos|ministry of health,? france|minist[eè]re de la sant", re.I)
KCE = re.compile(r"\bkce\b|knowledge cent(er|re)|belgian health care knowledge", re.I)

PATHO = [
    # (thème, pathologie, motif)
    ("Glomérulopathies / néphropathies immunes", "Néphropathie à IgA", r"iga nephropathy|immunoglobulin a nephropathy|\bigan\b|berger|iga vasculitis|henoch"),
    ("Glomérulopathies / néphropathies immunes", "Néphropathie lupique", r"lupus"),
    ("Glomérulopathies / néphropathies immunes", "Glomérulonéphrite extramembraneuse", r"membranous"),
    ("Glomérulopathies / néphropathies immunes", "HSF / syndrome néphrotique", r"fsgs|focal segmental|nephrotic|minimal change|podocyt"),
    ("Glomérulopathies / néphropathies immunes", "Vascularites à ANCA", r"anca|polyangiitis|vasculitis|anti-gbm|goodpasture"),
    ("Glomérulopathies / néphropathies immunes", "MAT / SHU", r"hemolytic uremic|haemolytic uraemic|\bahus\b|\bshu\b|thrombotic microangiopath|\btma\b"),
    ("Glomérulopathies / néphropathies immunes", "Glomérulopathie à C3", r"c3 glomerulopathy|\bc3g\b|dense deposit|membranoproliferative"),
    ("Glomérulopathies / néphropathies immunes", "Gammapathies / amylose", r"amyloid|monoclonal gammopathy|mgrs|myeloma|light chain"),
    ("Transplantation", "Rejet / désimmunisation", r"rejection|desensiti|hla|donor-specific|\bdsa\b|antibody-mediated"),
    ("Transplantation", "Immunosuppression / tolérance", r"immunosuppress|tacrolimus|belatacept|tolerance|induction|steroid withdrawal|calcineurin"),
    ("Transplantation", "Infections post-greffe", r"cmv|cytomegalovirus|bk ?virus|polyomavirus|infection|vaccin"),
    ("Transplantation", "Donneur / préservation du greffon", r"donor|perfusion|preservation|delayed graft function|ischemia-reperfusion|machine"),
    ("Dialyse / suppléance", "Hémodialyse / HDF", r"hemodialysis|haemodialysis|hemodiafiltration|haemodiafiltration|\bhdf\b"),
    ("Dialyse / suppléance", "Dialyse péritonéale", r"peritoneal dialysis"),
    ("Dialyse / suppléance", "Abord vasculaire", r"fistula|vascular access|catheter|arteriovenous"),
    ("Dialyse / suppléance", "Complications du dialysé (prurit, CV, nutrition…)", r"pruritus|cardiovascular|nutrition|frailty|exercise|depression|quality of life|calciphylaxis"),
    ("MRC / néphroprotection / cardio-rénal", "Maladie rénale diabétique", r"diabet"),
    ("MRC / néphroprotection / cardio-rénal", "HTA / cardio-rénal", r"hypertension|heart failure|cardio"),
    ("MRC / néphroprotection / cardio-rénal", "Anémie", r"anemia|anaemia"),
    ("MRC / néphroprotection / cardio-rénal", "Hyperkaliémie / acidose", r"hyperkal|potassium|acidosis"),
    ("MRC / néphroprotection / cardio-rénal", "Troubles minéraux et osseux", r"phosph|parathyroid|mineral|bone|calcif|vitamin d"),
    ("MRC / néphroprotection / cardio-rénal", "Progression de la MRC", r"chronic kidney|\bckd\b|progression|egfr decline|albuminuri|proteinuri|sglt2|finerenone"),
    ("Maladies rénales rares / génétiques", "Polykystose (PKD)", r"polycystic|adpkd|arpkd"),
    ("Maladies rénales rares / génétiques", "Syndrome d'Alport", r"alport|collagen iv"),
    ("Maladies rénales rares / génétiques", "Maladie de Fabry", r"fabry"),
    ("Maladies rénales rares / génétiques", "Cystinose", r"cystinosis"),
    ("Maladies rénales rares / génétiques", "Hyperoxalurie", r"hyperoxaluria|oxalate"),
    ("Maladies rénales rares / génétiques", "Tubulopathies / hypophosphatémies", r"tubulopath|gitelman|bartter|hypophosphat|cystinuria|dent"),
    ("Insuffisance rénale aiguë", "IRA post-chirurgicale", r"cardiac surgery|surgery|postoperative|perioperative"),
    ("Insuffisance rénale aiguë", "IRA en réanimation / sepsis", r"sepsis|septic|intensive care|critically ill|\bicu\b|shock"),
    ("Insuffisance rénale aiguë", "Néphropathie aux produits de contraste / toxiques", r"contrast|nephrotox|rhabdomyolysis|cisplatin"),
    ("Lithiase / infections urinaires", "Lithiase", r"lithiasis|lithiase|lithotri|nephrolith|urolith|stone|calcul|calic|calyx|colic|residual fragment"),
    ("Lithiase / infections urinaires", "Infections urinaires", r"pyelonephritis|pyélonéphrite|urinary tract infection|infection urinaire"),
    ("Autre néphrologie", "Néphrologie anténatale et uropathies de l'enfant", r"fetal|fetus|fœt|foet|antenatal|prenatal|anténatal|neonat|nouveau-né|posterior urethral|valves de l'urètre|"
                                                                              r"uretero-?pelvic|pyelo-?ureteral|jonction pyélo|cakut|spina bifida|neurogenic bladder|vessie neurologique|vesico-?ureteral|enuresis|énurésie"),
    ("Autre néphrologie", "Rein et grossesse", r"pregnan|grossesse|preeclampsia|pré-?éclampsie"),
    ("Autre néphrologie", "Atteintes rénales des maladies systémiques", r"wilson|myopath|myosit|sarcoid|systemic sclerosis|scleroderma|sclérodermie|sickle|drépanocyt|lupus|"
                                                                        r"tuberous sclerosis|sclérose tubéreuse|enamel renal|diabetes insipidus|diabète insipide|hnf1b|tcf2|chlordecone"),
    ("Autre néphrologie", "Néphrotoxicité et pharmacologie", r"drug-induced|interstitial nephritis|néphrite interstitielle|nephrotox|néphrotox|lithium|hyperclearance|"
                                                             r"augmented renal clearance|pharmacokinetic|pharmacocinétique|drug monitoring|dosing|checkpoint|ceftriaxone|beta-lactam"),
    ("Autre néphrologie", "Imagerie, chirurgie et radiologie interventionnelle", r"imaging|imagerie|renogram|scintigra|spect|\bmri\b|\birm\b|angiograph|ultrasound|échograph|"
                                                                                 r"nephron-sparing|nephrectomy|néphrectomie|surgery|chirurgi|3d|clamping|stent|endovascular|cyst|kyste"),
]
