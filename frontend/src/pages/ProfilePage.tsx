import { SaveIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../api";
import type { Profile } from "../types";

const empty: Profile = {
  nombre: "",
  skills: "",
  experiencia_anos: 0,
  nivel: "",
  modalidad_preferida: "",
  otras_preferencias: "",
};

export default function ProfilePage() {
  const [form, setForm] = useState<Profile>(empty);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.getProfile().then(setForm).catch(() => {});
  }, []);

  function set(field: keyof Profile, value: string | number) {
    setForm((p) => ({ ...p, [field]: value }));
    setSaved(false);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.updateProfile(form);
      setSaved(true);
    } catch (err) {
      alert("Error al guardar: " + (err as Error).message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-8">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Mi Perfil</h2>
        <p className="text-gray-500 mt-1">
          La IA usa estos datos para evaluar qué ofertas son más relevantes para vos.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Nombre</label>
          <input
            type="text"
            value={form.nombre}
            onChange={(e) => set("nombre", e.target.value)}
            placeholder="Tu nombre"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-rose-400"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Skills y habilidades <span className="text-red-500">*</span>
          </label>
          <textarea
            value={form.skills}
            onChange={(e) => set("skills", e.target.value)}
            rows={4}
            placeholder="Ej: Relaciones Públicas, Comunicación Corporativa, Gestión de Crisis, Redes Sociales, Adobe Suite, SEO, Redacción periodística..."
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-rose-400 resize-none"
          />
          <p className="text-xs text-gray-400 mt-1">Listá tus habilidades separadas por coma. Cuanto más detallado, mejor el análisis.</p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Años de experiencia</label>
            <input
              type="number"
              min={0}
              max={40}
              value={form.experiencia_anos}
              onChange={(e) => set("experiencia_anos", Number(e.target.value))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-rose-400"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nivel</label>
            <select
              value={form.nivel}
              onChange={(e) => set("nivel", e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-rose-400 bg-white"
            >
              <option value="">Sin especificar</option>
              <option value="Junior">Junior (0–2 años)</option>
              <option value="Semi-Senior">Semi-Senior (2–4 años)</option>
              <option value="Senior">Senior (4+ años)</option>
              <option value="Lead / Manager">Lead / Manager</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Modalidad preferida</label>
          <select
            value={form.modalidad_preferida}
            onChange={(e) => set("modalidad_preferida", e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-rose-400 bg-white"
          >
            <option value="">Sin preferencia</option>
            <option value="Remoto">Remoto</option>
            <option value="Híbrido">Híbrido</option>
            <option value="Presencial">Presencial</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Otras preferencias</label>
          <textarea
            value={form.otras_preferencias}
            onChange={(e) => set("otras_preferencias", e.target.value)}
            rows={3}
            placeholder="Ej: Busco posiciones en empresas de tecnología o startups, con foco en comunicación interna, sueldo mínimo $X..."
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-rose-400 resize-none"
          />
        </div>

        <div className="flex items-center gap-3 pt-2">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 bg-rose-500 hover:bg-rose-600 disabled:opacity-50 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors"
          >
            <SaveIcon size={16} />
            {saving ? "Guardando..." : "Guardar perfil"}
          </button>
          {saved && <span className="text-sm text-green-600 font-medium">✓ Guardado</span>}
        </div>
      </form>
    </div>
  );
}
